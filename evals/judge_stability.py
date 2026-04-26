"""Judge stability check: re-score frozen agent outputs N times.

Pulls fixed outputs from the `fixed_outputs` table (no more regex of
markdown reports). Each stability check is its own `runs` row tagged
'judge-stability'; per-trial verdicts go to `judge_stability_verdicts`.

If verdicts flip across identical inputs, the judge itself is noisy —
flips you see during the main eval may not be agent drift but judge drift.
"""
import time

import db
from agent import SYSTEM_PROMPT
from data import reference_output
from judge import FAITHFULNESS_CRITERION, CorrectnessJudge
from report import write_report

TRIALS = 5
DEFAULT_CASE_NUMS = (5, 6, 7, 9)  # 1-indexed


def _select_fixed_outputs(conn, case_nums: tuple[int, ...]) -> list[dict]:
    """Pick the most-recent fixed_output per requested case."""
    out = []
    for n in case_nums:
        row = conn.execute(
            """
            SELECT fo.fixed_output_id, fo.agent_output, fo.case_id,
                   c.input AS case_input
            FROM fixed_outputs fo
            JOIN cases c ON c.case_id = fo.case_id
            WHERE c.case_id = (SELECT case_id FROM cases ORDER BY case_id LIMIT 1 OFFSET ?)
            ORDER BY fo.fixed_output_id DESC
            LIMIT 1
            """,
            (n - 1,),
        ).fetchone()
        if row is not None:
            out.append(dict(row))
    return out


async def run_judge_stability(
    case_nums: tuple[int, ...] = DEFAULT_CASE_NUMS,
    trials: int = TRIALS,
) -> None:
    conn = db.connect()
    fixed = _select_fixed_outputs(conn, case_nums)
    if not fixed:
        print("No fixed_outputs available; run scripts/migrate_golden.py first.")
        return

    judge = CorrectnessJudge()
    run_id = db.insert_run(
        conn,
        agent_model="(none — fixed outputs)",
        agent_system_prompt=SYSTEM_PROMPT,
        trials_per_case=trials,
        judge_models={judge.name: judge.model},
        judge_prompt_versions={judge.name: judge.PROMPT_VERSION},
        judge_temperatures={judge.name: 0.0},
        tag="judge-stability",
    )
    print(f"stability run_id={run_id}")

    per_case = []
    start = time.perf_counter()

    for fx in fixed:
        case_id = fx["case_id"]
        criterion_ids = db.get_correctness_criterion_ids(conn, case_id)
        criteria_text = [
            r["text"] for r in conn.execute(
                "SELECT text FROM criteria WHERE case_id = ? AND judge_name = 'correctness' ORDER BY idx",
                (case_id,),
            ).fetchall()
        ]
        # Use case_idx (0-based) to look up reference output from the in-memory dataset.
        case_idx_row = conn.execute(
            "SELECT COUNT(*) AS n FROM cases WHERE case_id < ?", (case_id,)
        ).fetchone()
        ref = reference_output(case_idx_row["n"])

        print(f"\n--- case_id {case_id}: {fx['case_input'][:80]} ---")
        verdicts, confidences, reasonings = [], [], []
        for t in range(trials):
            result = judge.evaluate(fx["case_input"], fx["agent_output"], criteria_text, ref)
            verdicts.append(result.label)
            confidences.append(result.confidence)
            reasonings.append(result.reasoning)
            print(f"[case {case_id} judge {t + 1}] {result.label} (conf {result.confidence})")
            for j, cr in enumerate(result.per_criterion):
                conn.execute(
                    """
                    INSERT INTO judge_stability_verdicts (
                        run_id, fixed_output_id, trial_idx, criterion_id,
                        judge_name, judge_model, score, confidence, reasoning, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id, fx["fixed_output_id"], t + 1, criterion_ids[j],
                        judge.name, judge.model,
                        {"pass": 1, "fail": 0}.get(cr.label),
                        cr.confidence, cr.reasoning, db.now(),
                    ),
                )
        conn.commit()

        pass_n = verdicts.count("pass")
        fail_n = verdicts.count("fail")
        agreement = max(pass_n, fail_n) / trials
        per_case.append({
            "fixed_output_id": fx["fixed_output_id"],
            "case_id": case_id,
            "input": fx["case_input"],
            "criteria": criteria_text,
            "output": fx["agent_output"],
            "verdicts": verdicts,
            "confidences": confidences,
            "reasonings": reasonings,
            "pass_n": pass_n,
            "fail_n": fail_n,
            "agreement": agreement,
        })

    db.finalize_run(conn, run_id)
    elapsed = time.perf_counter() - start
    overall = sum(c["agreement"] for c in per_case) / len(per_case)
    stable = all(c["agreement"] == 1.0 for c in per_case)
    diagnosis = (
        "STABLE -- judge is consistent across all cases; flips during eval reflect agent output drift"
        if stable
        else "UNSTABLE -- judge itself is noisy on at least one case; flips aren't purely agent drift"
    )

    lines = [
        f"# Judge Stability Check -- run {run_id}",
        "",
        "## Summary",
        "",
        f"- **Source:** fixed_outputs (DB)",
        f"- **Cases:** {', '.join(str(c['case_id']) for c in per_case)}",
        f"- **Trials per case:** {trials} (judge calls only, fixed agent output)",
        f"- **Mean agreement:** {overall:.0%}",
        f"- **Diagnosis:** {diagnosis}",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Per-case agreement",
        "",
        "| Case | Pass | Fail | Agreement |",
        "|------|------|------|-----------|",
        *[
            f"| {c['case_id']} | {c['pass_n']} | {c['fail_n']} | {c['agreement']:.0%} |"
            for c in per_case
        ],
        "",
    ]

    for c in per_case:
        lines += [
            f"## Case {c['case_id']}",
            "",
            f"**Input:** {c['input']}",
            "",
            "**Judge criteria:**",
            "",
            *[f"{j + 1}. {crit}" for j, crit in enumerate(c["criteria"])],
            "",
            "**Fixed agent output:**",
            "",
            "```",
            c["output"],
            "```",
            "",
            "**Per-trial verdicts:**",
            "",
            "| Trial | Verdict | Confidence | Reasoning |",
            "|-------|---------|------------|-----------|",
            *[
                f"| {i + 1} | {v} | {conf} | {r.replace('|', '\\|')} |"
                for i, (v, conf, r) in enumerate(zip(c["verdicts"], c["confidences"], c["reasonings"]))
            ],
            "",
        ]

    summary = "\n".join(lines)
    print("\n\n" + summary)
    path = write_report("judge-check", summary)
    print(f"\nReport saved to {path.name}")
    conn.close()
