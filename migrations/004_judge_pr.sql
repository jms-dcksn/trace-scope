-- Slice 5: persist judge-pr results so the UI can render P/R/F1 without re-running the judge.
-- One judge_pr_runs row per `evals judge-pr` invocation; one judge_pr_rows row per
-- (fixed_output, criterion) example evaluated.

CREATE TABLE IF NOT EXISTS judge_pr_runs (
    judge_pr_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_name      TEXT NOT NULL,
    judge_model     TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    elapsed_ms      INTEGER NOT NULL,
    tp              INTEGER NOT NULL,
    fp              INTEGER NOT NULL,
    tn              INTEGER NOT NULL,
    fn              INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    auto_labeled    INTEGER NOT NULL,
    precision_pct   REAL NOT NULL,
    recall_pct      REAL NOT NULL,
    f1_pct          REAL NOT NULL,
    accuracy_pct    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS judge_pr_rows (
    judge_pr_row_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_pr_run_id  INTEGER NOT NULL REFERENCES judge_pr_runs(judge_pr_run_id) ON DELETE CASCADE,
    fixed_output_id  INTEGER NOT NULL REFERENCES fixed_outputs(fixed_output_id),
    criterion_id     INTEGER NOT NULL REFERENCES criteria(criterion_id),
    case_id          INTEGER NOT NULL REFERENCES cases(case_id),
    gold             TEXT NOT NULL,    -- 'pass' | 'fail'
    predicted        TEXT NOT NULL,    -- 'pass' | 'fail' | 'unknown'
    outcome          TEXT NOT NULL,    -- 'TP' | 'FP' | 'TN' | 'FN' | 'SKIP'
    labeler          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_judge_pr_rows_run ON judge_pr_rows(judge_pr_run_id);
CREATE INDEX IF NOT EXISTS ix_judge_pr_runs_judge ON judge_pr_runs(judge_name, started_at);

PRAGMA user_version = 4;
