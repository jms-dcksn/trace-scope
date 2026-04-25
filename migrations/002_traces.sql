-- Slice 3: traces table + trials.trace_id FK.
-- One trace per trial — same string the faithfulness judge already builds.

CREATE TABLE IF NOT EXISTS traces (
    trace_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

ALTER TABLE trials ADD COLUMN trace_id INTEGER REFERENCES traces(trace_id);

CREATE INDEX IF NOT EXISTS ix_trials_trace ON trials(trace_id);

PRAGMA user_version = 2;
