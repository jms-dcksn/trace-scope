"""Thin SQLite wrapper for the eval harness.

Stdlib only: one connection helper, one seeding call, per-table inserters.
No ORM, no migrations framework — PRAGMA user_version + hand-written
`migrations/NNN.sql` when needed.
"""
import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
SCHEMA_PATH = ROOT / "schema.sql"
MIGRATIONS_DIR = ROOT / "migrations"
DEFAULT_DB_PATH = ROOT / "evals.db"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _db_path() -> Path:
    override = os.environ.get("EVAL_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Bootstrap from schema.sql when fresh; run migrations/NNN.sql with NNN > user_version."""
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current == 0:
        conn.executescript(SCHEMA_PATH.read_text())
        current = conn.execute("PRAGMA user_version").fetchone()[0]

    if not MIGRATIONS_DIR.exists():
        return
    pending = sorted(
        (int(f.name.split("_", 1)[0]), f)
        for f in MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql")
    )
    for version, path in pending:
        if version > current:
            conn.executescript(path.read_text())


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Return a connection with FKs on, Row factory, schema applied."""
    p = path or _db_path()
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _apply_migrations(conn)
    return conn


def config_hash(
    agent_model: str,
    agent_system_prompt: str,
    trials_per_case: int,
    judge_models: dict[str, str],
    judge_prompt_versions: dict[str, str],
    judge_temperatures: dict[str, float],
) -> str:
    payload = {
        "agent_model": agent_model,
        "agent_system_prompt": agent_system_prompt,
        "trials_per_case": trials_per_case,
        "judge_models": judge_models,
        "judge_prompt_versions": judge_prompt_versions,
        "judge_temperatures": judge_temperatures,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def seed_cases_from_dataset(
    conn: sqlite3.Connection,
    dataset: list[dict[str, Any]],
    faithfulness_criterion: str,
) -> None:
    """Upsert cases + criteria. Idempotent on case.input."""
    ts = now()
    for case in dataset:
        conn.execute(
            """
            INSERT INTO cases (input, expected, tags, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(input) DO UPDATE SET
                expected = excluded.expected,
                tags     = excluded.tags
            """,
            (case["input"], case.get("expected"), json.dumps(case.get("tags") or []), ts),
        )
        row = conn.execute(
            "SELECT case_id FROM cases WHERE input = ?", (case["input"],)
        ).fetchone()
        case_id = row["case_id"]
        # Upsert each correctness criterion by (case_id, judge_name, idx) so
        # existing rows keep their criterion_id (FKs from criterion_verdicts).
        for idx, text in enumerate(case["criteria"], 1):
            conn.execute(
                """
                INSERT INTO criteria (case_id, judge_name, idx, text)
                VALUES (?, 'correctness', ?, ?)
                ON CONFLICT(case_id, judge_name, idx) DO UPDATE SET text = excluded.text
                """,
                (case_id, idx, text),
            )
        # Drop any trailing criteria if the dataset shrank, but only if unreferenced.
        max_idx = len(case["criteria"])
        conn.execute(
            """
            DELETE FROM criteria
            WHERE case_id = ? AND judge_name = 'correctness' AND idx > ?
              AND criterion_id NOT IN (SELECT criterion_id FROM criterion_verdicts)
            """,
            (case_id, max_idx),
        )

    # Single global faithfulness criterion with case_id = NULL.
    existing = conn.execute(
        "SELECT criterion_id FROM criteria WHERE case_id IS NULL AND judge_name = 'faithfulness' AND idx = 1"
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT INTO criteria (case_id, judge_name, idx, text) VALUES (NULL, 'faithfulness', 1, ?)",
            (faithfulness_criterion,),
        )
    else:
        conn.execute(
            "UPDATE criteria SET text = ? WHERE criterion_id = ?",
            (faithfulness_criterion, existing["criterion_id"]),
        )
    conn.commit()


def seed_case_expectations(
    conn: sqlite3.Connection,
    dataset: list[dict[str, Any]],
) -> None:
    """Upsert tool_use expectations + materialize matching criteria rows.

    For each dataset case carrying `expected_tools`, store the payload in
    case_expectations (kind='tool_use') and expand it into criteria rows
    (judge_name='tool_use') so verdict insertion uses the standard path.
    """
    from tool_use import expand_payload

    ts = now()
    for case in dataset:
        payload = case.get("expected_tools")
        if not payload:
            continue
        case_id = get_case_id(conn, case["input"])
        value = json.dumps(payload, sort_keys=True)

        # Upsert case_expectations: there's no UNIQUE constraint, so
        # delete-then-insert keeps it idempotent on (case_id, kind='tool_use').
        conn.execute(
            "DELETE FROM case_expectations WHERE case_id = ? AND kind = 'tool_use'",
            (case_id,),
        )
        conn.execute(
            """
            INSERT INTO case_expectations (case_id, kind, value, notes, created_at)
            VALUES (?, 'tool_use', ?, NULL, ?)
            """,
            (case_id, value, ts),
        )

        specs = expand_payload(payload)
        for idx, spec in enumerate(specs, 1):
            conn.execute(
                """
                INSERT INTO criteria (case_id, judge_name, idx, text)
                VALUES (?, 'tool_use', ?, ?)
                ON CONFLICT(case_id, judge_name, idx) DO UPDATE SET text = excluded.text
                """,
                (case_id, idx, spec.text),
            )
        # Drop trailing tool_use criteria if shrunk (only if unreferenced).
        conn.execute(
            """
            DELETE FROM criteria
            WHERE case_id = ? AND judge_name = 'tool_use' AND idx > ?
              AND criterion_id NOT IN (SELECT criterion_id FROM criterion_verdicts)
            """,
            (case_id, len(specs)),
        )
    conn.commit()


def get_tool_use_expectations(conn: sqlite3.Connection, case_id: int) -> dict | None:
    row = conn.execute(
        "SELECT value FROM case_expectations WHERE case_id = ? AND kind = 'tool_use'",
        (case_id,),
    ).fetchone()
    return json.loads(row["value"]) if row else None


def get_tool_use_criterion_ids(conn: sqlite3.Connection, case_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT criterion_id FROM criteria WHERE case_id = ? AND judge_name = 'tool_use' ORDER BY idx",
        (case_id,),
    ).fetchall()
    return [r["criterion_id"] for r in rows]


def get_case_id(conn: sqlite3.Connection, case_input: str) -> int:
    row = conn.execute("SELECT case_id FROM cases WHERE input = ?", (case_input,)).fetchone()
    if row is None:
        raise LookupError(f"case not found for input: {case_input[:60]}...")
    return row["case_id"]


def get_correctness_criterion_ids(conn: sqlite3.Connection, case_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT criterion_id FROM criteria WHERE case_id = ? AND judge_name = 'correctness' ORDER BY idx",
        (case_id,),
    ).fetchall()
    return [r["criterion_id"] for r in rows]


def get_faithfulness_criterion_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT criterion_id FROM criteria WHERE case_id IS NULL AND judge_name = 'faithfulness' AND idx = 1"
    ).fetchone()
    if row is None:
        raise LookupError("faithfulness criterion not seeded")
    return row["criterion_id"]


def insert_run(
    conn: sqlite3.Connection,
    *,
    agent_model: str,
    agent_system_prompt: str,
    trials_per_case: int,
    judge_models: dict[str, str],
    judge_prompt_versions: dict[str, str],
    judge_temperatures: dict[str, float],
    tag: str | None = None,
) -> int:
    h = config_hash(
        agent_model, agent_system_prompt, trials_per_case,
        judge_models, judge_prompt_versions, judge_temperatures,
    )
    cur = conn.execute(
        """
        INSERT INTO runs (
            started_at, agent_model, agent_system_prompt, trials_per_case,
            judge_models, judge_prompt_versions, judge_temperatures,
            config_hash, tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(), agent_model, agent_system_prompt, trials_per_case,
            json.dumps(judge_models, sort_keys=True),
            json.dumps(judge_prompt_versions, sort_keys=True),
            json.dumps(judge_temperatures, sort_keys=True),
            h, tag,
        ),
    )
    conn.commit()
    return cur.lastrowid


def finalize_run(conn: sqlite3.Connection, run_id: int) -> None:
    conn.execute("UPDATE runs SET ended_at = ? WHERE run_id = ?", (now(), run_id))
    conn.commit()


def insert_trace(conn: sqlite3.Connection, *, content: str) -> int:
    # ~4 chars/token is the standard back-of-envelope.
    token_count = len(content) // 4
    cur = conn.execute(
        "INSERT INTO traces (content, token_count, created_at) VALUES (?, ?, ?)",
        (content, token_count, now()),
    )
    return cur.lastrowid


def insert_trial(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    case_id: int,
    trial_idx: int,
    output: str,
    trace_id: int | None = None,
    latency_ms: int | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    cost_usd: float | None = None,
    error: str | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO trials (
            run_id, case_id, trial_idx, output, trace_id,
            latency_ms, tokens_in, tokens_out, cost_usd, error, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, case_id, trial_idx, output, trace_id,
         latency_ms, tokens_in, tokens_out, cost_usd, error, now()),
    )
    return cur.lastrowid


def insert_tool_call(
    conn: sqlite3.Connection,
    *,
    trial_id: int,
    idx: int,
    tool_name: str,
    args: dict[str, Any],
    result: str,
    latency_ms: int | None = None,
    tokens: int | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO tool_calls (trial_id, idx, tool_name, args, result, latency_ms, tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (trial_id, idx, tool_name, json.dumps(args, sort_keys=True), result, latency_ms, tokens),
    )
    return cur.lastrowid


def seed() -> None:
    """Manual seed: `python -m db`-style entrypoint for idempotent seeding."""
    from data import dataset
    from judge import FAITHFULNESS_CRITERION
    conn = connect()
    try:
        seed_cases_from_dataset(conn, dataset, FAITHFULNESS_CRITERION)
        seed_case_expectations(conn, dataset)
        n_cases = conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()["n"]
        n_crit = conn.execute("SELECT COUNT(*) AS n FROM criteria").fetchone()["n"]
        n_exp = conn.execute("SELECT COUNT(*) AS n FROM case_expectations").fetchone()["n"]
        print(f"seeded: {n_cases} cases, {n_crit} criteria, {n_exp} expectations -> {_db_path()}")
    finally:
        conn.close()


def insert_criterion_verdict(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    trial_id: int,
    criterion_id: int,
    judge_name: str,
    judge_model: str,
    label: str,
    confidence: int,
    reasoning: str,
    judge_latency_ms: int | None = None,
    judge_tokens_in: int | None = None,
    judge_tokens_out: int | None = None,
    judge_cost_usd: float | None = None,
) -> int:
    score = {"pass": 1, "fail": 0}.get(label)  # "unknown" → NULL
    cur = conn.execute(
        """
        INSERT INTO criterion_verdicts (
            run_id, trial_id, criterion_id, judge_name, judge_model,
            score, confidence, reasoning,
            judge_latency_ms, judge_tokens_in, judge_tokens_out, judge_cost_usd,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, trial_id, criterion_id, judge_name, judge_model,
         score, confidence, reasoning,
         judge_latency_ms, judge_tokens_in, judge_tokens_out, judge_cost_usd,
         now()),
    )
    return cur.lastrowid


if __name__ == "__main__":
    seed()
