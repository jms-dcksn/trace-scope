"""Judge precision/recall against gold_labels in the DB.

Aggregates per-criterion: each (fixed_output, criterion) pair is one example.
Treats `pass` as the positive class. Generalized over judge_name so the
same logic runs for correctness today and faithfulness once those gold
labels exist.
"""
import time

import db
from data import dataset, reference_output
from judge import CorrectnessJudge, FaithfulnessJudge
from report import write_report

JUDGES = {
    "correctness": CorrectnessJudge,
    "faithfulness": FaithfulnessJudge,
}


def _eval_correctness(judge, conn, fixed_output_id: int) -> dict[int, str]:
    """Returns {criterion_id: predicted_label} for one fixed output."""
    row = conn.execute(
        """
        SELECT fo.agent_output, c.case_id, c.input
        FROM fixed_outputs fo JOIN cases c ON c.case_id = fo.case_id
        WHERE fo.fixed_output_id = ?
        """,
        (fixed_output_id,),
    ).fetchone()
    crit_rows = conn.execute(
        "SELECT criterion_id, idx, text FROM criteria WHERE case_id = ? AND judge_name = 'correctness' ORDER BY idx",
        (row["case_id"],),
    ).fetchall()
    criterion_ids = [r["criterion_id"] for r in crit_rows]
    criteria = [r["text"] for r in crit_rows]
    case_idx = conn.execute(
        "SELECT COUNT(*) FROM cases WHERE case_id < ?", (row["case_id"],)
    ).fetchone()[0]
    ref = reference_output(case_idx)
    result = judge.evaluate(row["input"], row["agent_output"], criteria, ref)
    return {criterion_ids[i]: cr.label for i, cr in enumerate(result.per_criterion)}


def run_judge_precision_recall(judge_name: str = "correctness", model: str = "gpt-5.4") -> None:
    if judge_name not in JUDGES:
        raise SystemExit(f"unknown judge: {judge_name}")
    if judge_name == "faithfulness":
        # Faithfulness gold labels don't exist yet — needs trace + per-case hand labels.
        raise SystemExit(
            "faithfulness P/R needs gold_labels with judge_name='faithfulness'; "
            "Phase 2 §4 will land those."
        )

    judge = JUDGES[judge_name](model)
    conn = db.connect()

    # Pull every (fixed_output, criterion) pair with a gold label for this judge.
    pairs = conn.execute(
        """
        SELECT g.fixed_output_id, g.criterion_id, g.label AS gold,
               g.labeler, fo.case_id
        FROM gold_labels g
        JOIN fixed_outputs fo ON fo.fixed_output_id = g.fixed_output_id
        WHERE g.judge_name = ?
        ORDER BY g.fixed_output_id, g.criterion_id
        """,
        (judge_name,),
    ).fetchall()
    if not pairs:
        raise SystemExit(f"no gold_labels for judge_name={judge_name!r}")

    # Group by fixed_output_id so we run the judge once per output.
    by_output: dict[int, list[dict]] = {}
    for p in pairs:
        by_output.setdefault(p["fixed_output_id"], []).append(dict(p))

    tp = fp = tn = fn = 0
    rows = []
    auto_labeled = 0
    start = time.perf_counter()

    for fixed_output_id, items in by_output.items():
        predictions = _eval_correctness(judge, conn, fixed_output_id)
        for it in items:
            gold = it["gold"]                                # 1 or 0
            pred = predictions.get(it["criterion_id"], "unknown")
            pred_int = 1 if pred == "pass" else (0 if pred == "fail" else None)
            if pred_int is None:
                continue
            if pred_int == 1 and gold == 1:
                tp += 1; outcome = "TP"
            elif pred_int == 1 and gold == 0:
                fp += 1; outcome = "FP"
            elif pred_int == 0 and gold == 0:
                tn += 1; outcome = "TN"
            else:
                fn += 1; outcome = "FN"
            if it["labeler"] == "auto-from-case-level":
                auto_labeled += 1
            rows.append((fixed_output_id, it["criterion_id"], it["case_id"],
                         "pass" if gold == 1 else "fail", pred, outcome, it["labeler"]))

    elapsed = time.perf_counter() - start
    n = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / n if n else 0.0

    print(f"\nTP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Precision={precision:.2%}  Recall={recall:.2%}  F1={f1:.2%}  "
          f"Accuracy={accuracy:.2%}  ({elapsed:.1f}s)")

    lines = [
        f"# Judge Precision/Recall -- {judge_name}",
        "",
        f"- **Examples:** {n} (per-criterion)",
        f"- **TP/FP/TN/FN:** {tp}/{fp}/{tn}/{fn}",
        f"- **Precision:** {precision:.2%}",
        f"- **Recall:** {recall:.2%}",
        f"- **F1:** {f1:.2%}",
        f"- **Accuracy:** {accuracy:.2%}",
        f"- **Auto-labeled rows:** {auto_labeled}/{n} (cheap migration -- F1 not directly comparable to Phase 1)",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "| fixed_output_id | criterion_id | case_id | gold | predicted | outcome | labeler |",
        "|---|---|---|---|---|---|---|",
        *[f"| {fo} | {cid} | {ca} | {g} | {p} | {o} | {lab} |"
          for fo, cid, ca, g, p, o, lab in rows],
    ]
    path = write_report(f"judge-pr-{judge_name}", "\n".join(lines))
    print(f"\nReport saved to {path.name}")
    conn.close()
