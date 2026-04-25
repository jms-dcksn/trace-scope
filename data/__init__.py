from .dataset import dataset
from .golden_dataset import golden_dataset


def reference_output(case_idx: int) -> str | None:
    """Return the first pass-labeled fixed_output for a dataset case, if any.

    Reads from the DB (fixed_outputs joined to gold_labels). Falls back to None
    if the row hasn't been seeded yet — run scripts/migrate_golden.py first.
    """
    import db
    conn = db.connect()
    try:
        row = conn.execute(
            """
            SELECT fo.agent_output
            FROM fixed_outputs fo
            JOIN gold_labels g ON g.fixed_output_id = fo.fixed_output_id
            WHERE fo.case_id = (SELECT case_id FROM cases ORDER BY case_id LIMIT 1 OFFSET ?)
              AND g.judge_name = 'correctness'
              AND g.label = 1
            ORDER BY fo.fixed_output_id
            LIMIT 1
            """,
            (case_idx,),
        ).fetchone()
        return row["agent_output"] if row else None
    finally:
        conn.close()


__all__ = ["dataset", "golden_dataset", "reference_output"]
