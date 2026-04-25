-- Phase 2 Slice 1: write path. Six tables make the DB the system of record.
-- Analytical tables (traces, fixed_outputs, gold_labels, ...) arrive in slices 3-4.
-- Booleans stored as INTEGER 0/1. Timestamps are ISO-8601 UTC strings.

PRAGMA user_version = 1;

CREATE TABLE IF NOT EXISTS cases (
    case_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    input         TEXT NOT NULL UNIQUE,
    expected      TEXT,
    tags          TEXT NOT NULL DEFAULT '[]',   -- JSON array
    created_at    TEXT NOT NULL,
    archived_at   TEXT
);

-- Per-case correctness criteria live with case_id set.
-- Global faithfulness criterion lives with case_id = NULL.
CREATE TABLE IF NOT EXISTS criteria (
    criterion_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id       INTEGER REFERENCES cases(case_id) ON DELETE CASCADE,
    judge_name    TEXT NOT NULL,
    idx           INTEGER NOT NULL,
    text          TEXT NOT NULL,
    UNIQUE (case_id, judge_name, idx)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at              TEXT NOT NULL,
    ended_at                TEXT,
    agent_model             TEXT NOT NULL,
    agent_system_prompt     TEXT NOT NULL,
    trials_per_case         INTEGER NOT NULL,
    judge_models            TEXT NOT NULL,      -- JSON {judge_name: model}
    judge_prompt_versions   TEXT NOT NULL,      -- JSON {judge_name: version}
    judge_temperatures      TEXT NOT NULL,      -- JSON {judge_name: temp}
    config_hash             TEXT NOT NULL,
    tag                     TEXT
);

CREATE TABLE IF NOT EXISTS trials (
    trial_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    case_id       INTEGER NOT NULL REFERENCES cases(case_id),
    trial_idx     INTEGER NOT NULL,             -- 1-based within case within run
    output        TEXT NOT NULL,
    latency_ms    INTEGER,
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    cost_usd      REAL,
    created_at    TEXT NOT NULL,
    UNIQUE (run_id, case_id, trial_idx)
);

CREATE TABLE IF NOT EXISTS tool_calls (
    tool_call_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id      INTEGER NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    idx           INTEGER NOT NULL,             -- call order within the trial
    tool_name     TEXT NOT NULL,
    args          TEXT NOT NULL,                -- JSON
    result        TEXT NOT NULL,
    latency_ms    INTEGER,
    tokens        INTEGER
);

CREATE TABLE IF NOT EXISTS criterion_verdicts (
    verdict_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    trial_id            INTEGER NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    criterion_id        INTEGER NOT NULL REFERENCES criteria(criterion_id),
    judge_name          TEXT NOT NULL,
    judge_model         TEXT NOT NULL,
    score               INTEGER,                -- 1 pass, 0 fail, NULL unknown
    confidence          INTEGER NOT NULL,
    reasoning           TEXT NOT NULL,
    judge_latency_ms    INTEGER,
    judge_tokens_in     INTEGER,
    judge_tokens_out    INTEGER,
    judge_cost_usd      REAL,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_trials_run ON trials(run_id);
CREATE INDEX IF NOT EXISTS ix_verdicts_run ON criterion_verdicts(run_id);
CREATE INDEX IF NOT EXISTS ix_verdicts_trial ON criterion_verdicts(trial_id);
CREATE INDEX IF NOT EXISTS ix_tool_calls_trial ON tool_calls(trial_id);
