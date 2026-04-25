-- Slice 4: calibration substrate.
-- fixed_outputs: canonical agent outputs frozen for judge calibration.
-- gold_labels:   ground-truth pass/fail per (criterion, fixed_output, judge).
-- judge_stability_verdicts: results of repeated judge runs on a fixed output.
-- case_expectations: per-case expectations for ToolUseJudge (Phase 2 §8).

CREATE TABLE IF NOT EXISTS fixed_outputs (
    fixed_output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER NOT NULL REFERENCES cases(case_id),
    agent_output    TEXT NOT NULL,
    notes           TEXT,
    trace           TEXT,
    source          TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gold_labels (
    gold_label_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion_id    INTEGER NOT NULL REFERENCES criteria(criterion_id),
    fixed_output_id INTEGER NOT NULL REFERENCES fixed_outputs(fixed_output_id),
    judge_name      TEXT NOT NULL,
    label           INTEGER NOT NULL,
    labeler         TEXT NOT NULL,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    UNIQUE (criterion_id, fixed_output_id, judge_name)
);

CREATE TABLE IF NOT EXISTS judge_stability_verdicts (
    stability_verdict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    fixed_output_id INTEGER NOT NULL REFERENCES fixed_outputs(fixed_output_id),
    trial_idx       INTEGER NOT NULL,
    criterion_id    INTEGER NOT NULL REFERENCES criteria(criterion_id),
    judge_name      TEXT NOT NULL,
    judge_model     TEXT NOT NULL,
    score           INTEGER,
    confidence      INTEGER NOT NULL,
    reasoning       TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_expectations (
    expectation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id        INTEGER NOT NULL REFERENCES cases(case_id),
    kind           TEXT NOT NULL,
    value          TEXT NOT NULL,
    notes          TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_gold_labels_fixed_output ON gold_labels(fixed_output_id);
CREATE INDEX IF NOT EXISTS ix_gold_labels_criterion ON gold_labels(criterion_id);
CREATE INDEX IF NOT EXISTS ix_stability_run ON judge_stability_verdicts(run_id);

PRAGMA user_version = 3;
