-- Human review annotations on verdicts + trials, plus small schema gaps.
-- failure_mode is a low-cardinality string constrained in the UI (not the DB)
-- so the bucket list can iterate cheaply: agent-error, judge-too-strict,
-- judge-too-lenient, gold-wrong, criterion-ambiguous, other.

ALTER TABLE criterion_verdicts ADD COLUMN reviewer_notes TEXT;
ALTER TABLE criterion_verdicts ADD COLUMN failure_mode TEXT;
ALTER TABLE criterion_verdicts ADD COLUMN reviewed_at TEXT;
ALTER TABLE trials ADD COLUMN reviewer_notes TEXT;

-- Schema gaps: capture agent crashes instead of failing the whole run,
-- and a cheap token-count estimate for traces.
ALTER TABLE trials ADD COLUMN error TEXT;
ALTER TABLE traces ADD COLUMN token_count INTEGER;

PRAGMA user_version = 7;
