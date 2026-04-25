# agent-eval-phase-1

An eval harness for a Tavily-search LangChain agent. SQLite is the system of record; markdown reports are rendered from it.

## Setup

```bash
uv sync
export OPENAI_API_KEY=...
export TAVILY_API_KEY=...
uv run python db.py                       # seed cases + criteria
uv run python scripts/migrate_golden.py   # seed fixed_outputs + gold_labels
```

## Run

```bash
uv run python -m evals run                # full dataset
uv run python -m evals run --cases 3-5-7  # subset (1-indexed)
uv run python -m evals history            # list runs
uv run python -m evals report <run_id>    # render markdown from DB
uv run python -m evals compare <a> <b>    # per-criterion deltas + Wilson CIs
uv run python -m evals judge-check        # judge stability on fixed outputs
uv run python -m evals judge-pr           # judge precision/recall vs gold
```

## What's where

- `agent.py` — Tavily-search LangChain agent under test
- `judge.py` — `CorrectnessJudge` (per-criterion) and `FaithfulnessJudge` (grounded-in-evidence)
- `evals/run_eval.py` — orchestrator: agent N times per case, scored, written to DB
- `evals/report_from_db.py`, `evals/compare.py` — read path
- `db.py`, `schema.sql`, `migrations/` — SQLite layer; `evals.db` lives at repo root
- `data/dataset.py` — eval cases; `data/golden_dataset.py` — hand-labeled outputs

## Conventions worth knowing

- Bump `PROMPT_VERSION` on a judge whenever you edit its prompt — it feeds `config_hash`, which `compare` uses to flag apples-to-oranges runs.
- Schema changes are `migrations/NNN_*.sql` ending with `PRAGMA user_version = N;`. Don't edit existing migrations.
- Judge metrics (latency, tokens, cost) are written to the *first* verdict row of each call only — `SUM(judge_cost_usd)` stays honest, `AVG` does not.

## Deeper context

`CLAUDE.md` for architecture and conventions. `../projects/01-agent-eval-harness-plan.md` for the canonical design doc and rationale.
