"""One-shot migration: golden_dataset.py → fixed_outputs + gold_labels.

Cheap migration: per-criterion label inherits the case-level gold_label, with
labeler='auto-from-case-level' so it's obvious the rows are degraded. Hand-
relabel the surprises after running judge-pr once to find them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from data import dataset, golden_dataset


def main() -> None:
    conn = db.connect()
    inserted_outputs = 0
    inserted_labels = 0
    skipped_outputs = 0

    for item in golden_dataset:
        case_idx = item["case_idx"]
        case = dataset[case_idx]
        case_id = db.get_case_id(conn, case["input"])

        # Idempotent: skip if (case_id, agent_output) already exists.
        existing = conn.execute(
            "SELECT fixed_output_id FROM fixed_outputs WHERE case_id = ? AND agent_output = ?",
            (case_id, item["output"]),
        ).fetchone()
        if existing is not None:
            skipped_outputs += 1
            fixed_output_id = existing["fixed_output_id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO fixed_outputs (case_id, agent_output, notes, source, created_at)
                VALUES (?, ?, ?, 'golden_dataset.py', ?)
                """,
                (case_id, item["output"], item.get("notes"), db.now()),
            )
            fixed_output_id = cur.lastrowid
            inserted_outputs += 1

        label_int = 1 if item["gold_label"] == "pass" else 0
        criterion_ids = db.get_correctness_criterion_ids(conn, case_id)
        for criterion_id in criterion_ids:
            conn.execute(
                """
                INSERT INTO gold_labels (
                    criterion_id, fixed_output_id, judge_name,
                    label, labeler, notes, created_at
                ) VALUES (?, ?, 'correctness', ?, 'auto-from-case-level', ?, ?)
                ON CONFLICT(criterion_id, fixed_output_id, judge_name) DO NOTHING
                """,
                (criterion_id, fixed_output_id, label_int, item.get("notes"), db.now()),
            )
            inserted_labels += conn.total_changes and 1 or 0  # informational only

    conn.commit()
    print(
        f"fixed_outputs: +{inserted_outputs} (skipped {skipped_outputs} dupes)  "
        f"gold_labels written for {len(golden_dataset)} outputs"
    )
    print(
        f"totals: fixed_outputs={conn.execute('SELECT COUNT(*) FROM fixed_outputs').fetchone()[0]}, "
        f"gold_labels={conn.execute('SELECT COUNT(*) FROM gold_labels').fetchone()[0]}"
    )


if __name__ == "__main__":
    main()
