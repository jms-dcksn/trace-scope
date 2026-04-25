"""CLI entrypoint: `python -m evals {run|report|compare|history|judge-check|judge-pr}`."""
import argparse
import asyncio

import db
from data import dataset

from .compare import render_and_save as compare_save
from .judge_precision_recall import run_judge_precision_recall
from .judge_stability import run_judge_stability
from .report_from_db import render_and_save as report_save
from .run_eval import run_dataset_eval as _run_dataset


def _parse_indices(arg: str) -> list[int]:
    indices = [int(p) - 1 for p in arg.split("-") if p]
    for i in indices:
        if i < 0 or i >= len(dataset):
            raise SystemExit(f"Index {i + 1} out of range (1..{len(dataset)})")
    return indices


def _cmd_run(args) -> None:
    indices = _parse_indices(args.cases) if args.cases else None
    asyncio.run(_run_dataset(indices))


def _cmd_report(args) -> None:
    name = report_save(args.run_id)
    print(f"report saved to {name}")


def _cmd_compare(args) -> None:
    name = compare_save(args.run_a, args.run_b)
    print(f"compare saved to {name}")


def _cmd_history(args) -> None:
    conn = db.connect()
    rows = conn.execute(
        """
        SELECT r.run_id, r.started_at, r.ended_at, r.agent_model, r.tag,
               COUNT(DISTINCT t.case_id) AS cases,
               COUNT(t.trial_id)         AS trials,
               SUBSTR(r.config_hash, 1, 12) AS cfg
        FROM runs r
        LEFT JOIN trials t ON t.run_id = r.run_id
        GROUP BY r.run_id
        ORDER BY r.run_id DESC
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()
    print(f"{'id':>4}  {'started':25s}  {'model':22s}  {'cases':>5}  {'trials':>6}  {'cfg':12s}  tag")
    for r in rows:
        print(
            f"{r['run_id']:>4}  {r['started_at']:25s}  "
            f"{(r['agent_model'] or ''):22s}  {r['cases']:>5}  {r['trials']:>6}  "
            f"{r['cfg']:12s}  {r['tag'] or ''}"
        )


def _cmd_judge_check(args) -> None:
    case_nums = tuple(int(p) for p in args.cases.split("-")) if args.cases else (5, 6, 7, 9)
    asyncio.run(run_judge_stability(case_nums=case_nums, trials=args.trials))


def _cmd_judge_pr(args) -> None:
    run_judge_precision_recall(judge_name=args.judge)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="evals")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run dataset eval (agent x dataset)")
    run.add_argument("--cases", help="dash-separated 1-indexed case numbers, e.g. 3-5-7")
    run.set_defaults(func=_cmd_run)

    rep = sub.add_parser("report", help="render markdown report for a run_id")
    rep.add_argument("run_id", type=int)
    rep.set_defaults(func=_cmd_report)

    cmp = sub.add_parser("compare", help="compare two runs by per-criterion pass rate")
    cmp.add_argument("run_a", type=int)
    cmp.add_argument("run_b", type=int)
    cmp.set_defaults(func=_cmd_compare)

    hist = sub.add_parser("history", help="list recent runs")
    hist.add_argument("--limit", type=int, default=20)
    hist.set_defaults(func=_cmd_history)

    jc = sub.add_parser("judge-check", help="judge stability on fixed outputs")
    jc.add_argument("--cases", help="dash-separated 1-indexed case numbers (default 5-6-7-9)")
    jc.add_argument("--trials", type=int, default=5)
    jc.set_defaults(func=_cmd_judge_check)

    jpr = sub.add_parser("judge-pr", help="judge precision/recall against gold_labels")
    jpr.add_argument("--judge", default="correctness", choices=("correctness", "faithfulness"))
    jpr.set_defaults(func=_cmd_judge_pr)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
