-- Judge prompts as versioned artifacts in the DB.
-- Templates use Python str.format_map() with named placeholders the judge
-- code computes (e.g. {numbered_criteria}, {evidence_block}). Only the
-- prose around the placeholders is editable from the UI.

CREATE TABLE IF NOT EXISTS judge_prompts (
    judge_prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_name      TEXT NOT NULL,
    version         TEXT NOT NULL,
    template        TEXT NOT NULL,
    notes           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE (judge_name, version)
);

-- One active version per judge_name.
CREATE UNIQUE INDEX IF NOT EXISTS ux_judge_prompts_active
    ON judge_prompts(judge_name) WHERE is_active = 1;

PRAGMA user_version = 5;
