# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An eval harness for a Tavily-search LangChain agent. Phase 1 was markdown reports; Phase 2 (current) puts SQLite at the center as the system of record for runs, trials, tool calls, and judge verdicts. The canonical design doc lives at `../projects/01-agent-eval-harness-plan.md` — read that for *why* the schema looks the way it does. `PLAN.md` (gitignored) is the implementation sequencing for Phase 2.

## Commands

```bash
uv run python -m evals run                  # full dataset eval
uv run python -m evals run --cases 3-5-7    # 1-indexed subset
uv run python -m evals report <run_id>      # render markdown from DB
uv run python -m evals compare <a> <b>      # per-criterion deltas + Wilson CIs
uv run python -m evals history              # list recent runs
uv run python -m evals judge-check          # judge stability on fixed_outputs
uv run python -m evals judge-pr --judge correctness   # P/R against gold_labels

uv run python db.py                         # idempotent seed: cases + criteria
uv run python scripts/migrate_golden.py     # one-shot: golden_dataset.py -> fixed_outputs + gold_labels
```

`main.py` is a thin shim over the `evals` CLI for legacy invocations (`uv run main.py 1`, `uv run main.py judge-check`). Prefer the new CLI for new work.

`TAVILY_API_KEY` and `OPENAI_API_KEY` must be set in the environment.

## Architecture

**SQLite is the source of truth.** Markdown in `results/` is rendered *from* the DB (`evals/report_from_db.py`), not the canonical log. `evals.db` lives at the repo root and is gitignored.

**Schema lives in two places.** `schema.sql` is the bootstrap for fresh DBs; `migrations/NNN_*.sql` evolve existing ones. `db.connect()` reads `PRAGMA user_version`, applies `schema.sql` on a fresh DB, then runs any migrations whose number exceeds the current version. To change schema: write a new `migrations/NNN_*.sql` ending with `PRAGMA user_version = N;`. Don't edit existing migrations.

**Execution flow.** `evals/run_eval.py` orchestrates: insert a `runs` row → for each case, for each trial: agent run → write trace → write trial row → write tool_calls → run each judge → write verdicts. Commits per case for crash safety.

**Agent (`agent.py`)** wraps LangChain's `create_agent` with timing (`time.perf_counter`) and per-tool-call latency tracked via `ContextVar` (so `web_search` records its own latency without changing its return signature). Token totals come from summing `usage_metadata` across `AIMessage`s in the result.

**Judges (`judge.py`)** share a `BaseJudge` that uses `with_structured_output(..., include_raw=True)` so the raw `AIMessage` (and its `usage_metadata`) is available alongside the parsed Pydantic verdict. `CorrectnessJudge` evaluates per-criterion against the case's criteria; `FaithfulnessJudge` checks grounding against the rendered evidence trace. Both export `PROMPT_VERSION` — see Conventions.

**Cost (`costs.py`)** is hard-coded `MODEL_COSTS = {model: (input_per_1k, output_per_1k)}`. No live pricing fetch. Bump entries when rates change. `normalize_model` strips the `openai:` provider prefix that LangChain uses.

**Calibration substrate (slice 4).** `fixed_outputs` are frozen agent outputs for repeatable judge calibration. `gold_labels` carry per-criterion ground truth. `judge_stability_verdicts` log repeated judge calls on the same fixed output — its own `runs` row tagged `judge-stability`. `case_expectations` is provisioned for `ToolUseJudge` but has no writers yet.

## Conventions

- **`PROMPT_VERSION` discipline.** Every judge class has a manually-bumped `PROMPT_VERSION`. It feeds `config_hash` (sha256 of agent + judge config in `db.config_hash`). If you edit a judge prompt and forget to bump, `compare` will silently mislead because runs hash-equal. Bump it.
- **Judge metrics on first verdict row only.** A judge call covers all criteria for a trial in one LLM invocation. To keep `SUM(judge_cost_usd)` honest, only the first criterion's row gets the metrics; subsequent rows have NULL `judge_*` fields. Aggregations should rely on `SUM` (which ignores NULLs), not `AVG`.
- **Booleans as `INTEGER 0/1`.** Score column allows NULL for `unknown` verdicts.
- **Timestamps are ISO-8601 UTC strings** via `db.now()` (`datetime.now(UTC).isoformat(timespec='seconds')`). Text sorts correctly.
- **`PRAGMA foreign_keys = ON`** is set on every connection; SQLite doesn't enforce by default.
- **Case `input` is the natural key.** Seeding (`db.seed_cases_from_dataset`) upserts on it. Criteria upsert on `(case_id, judge_name, idx)` so existing `criterion_id`s stay stable for FKs from `criterion_verdicts`.
- **Faithfulness criterion is global** — one row in `criteria` with `case_id = NULL`, `judge_name = 'faithfulness'`, referenced by every faithfulness verdict.
- **`tool_calls.tokens` is NULL** because Tavily is an HTTP API with no LLM tokens. Pulling deliberation tokens from the agent's message array is parked post-MVP — see the reflection note in `../projects/01-agent-eval-harness-plan.md` §3.

## When extending

- New table or column → new `migrations/NNN_*.sql` with a `PRAGMA user_version` bump at the end. Update `schema.sql` only if you also want fresh DBs to skip the migration (rarely worth the duplication).
- New judge → subclass `BaseJudge`, add `PROMPT_VERSION`, register in `evals.judge_precision_recall.JUDGES`, seed a row in `criteria` if it's case-scoped.
- New CLI subcommand → add to `evals/__main__.py:build_parser`. `main.py` will pick it up automatically for argparse-style invocations.
