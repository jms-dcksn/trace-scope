# UI UX restructure — design

Date: 2026-04-26
Scope: Functional and information-architecture redesign of the eval UI. No
aesthetic overhaul.

## Goal

Make the UI orient around the right nouns and remove the "two systems for the
same thing" feel. Cases become the primary entry point; the golden dataset is
folded into a Case's detail page. Run detail stays as an aggregate; the trial
view becomes the comprehensive single-execution surface. New top-level pages
document the agent harness and the judges with their prompt-version history.

## Sitemap

```
/                       Home / dashboard
/cases                  Cases index (primary entry point)
/cases/[id]             Case detail — definition, golden record, trial history
/runs                   Runs index
/runs/[id]              Run rollup
/runs/[id]/trials/[tid] Trial detail (the comprehensive view)
/runs/compare           A/B compare (existing)
/agent                  Agent harness reference + inspector
/judges                 Judges hub (P/R/F1 cards + recent judge-pr runs)
/judges/[name]          Per-judge home — config, prompt history, gold stats
/judges/[name]/[promptId]   Specific historical prompt version
```

Top nav: **Cases · Runs · Agent · Judges**.

Removed as nav destinations: `/golden` (folded into Case detail) and
`/prompts` (folded into per-judge page). Existing routes can either redirect
or be deleted; preference is to delete to keep the surface honest.

## Page-by-page

### `/cases` — index

Table columns: Case input, # criteria, # fixed outputs, gold coverage
(correctness `pass/total`, faithfulness `pass/total`, with auto vs hand
counts), last trial (run id + pass/fail summary), tags.

Filters: needs-labels (any criterion lacking a gold label), has-failures (most
recent trial failed), tag.

Each row links to `/cases/[id]`.

### `/cases/[id]` — case detail

Three sections, stacked:

1. **Definition** — input, expected (if any), criteria editor. Existing
   behavior preserved (criterion edits go through `updateCriterion` server
   action; `PROMPT_VERSION` warning copy stays).
2. **Golden record** — list of `fixed_outputs` for this case. Each item is a
   collapsible block showing the frozen agent output and gold labels per
   criterion (with auto/hand badge), with inline edit forms moved over from
   `/golden/[id]`. This replaces `/golden/[id]` as a destination.
3. **Trial history** — every trial that has ever run this case across all
   runs, newest first. Columns: run id, started, attempt, pass/total per
   judge, latency, cost, link to trial detail.

### `/runs/[id]` — run rollup

Sharpened, not redesigned.

- Header gets a one-line summary line: `agent_model · N cases · M trials ·
  total cost · p50/p95 latency · overall pass rate`.
- Per-case rollup table stays.
- Right rail: existing **Failure modes** plus the **Judges used** block
  moved over from its own section, rendered as a compact list with links to
  `/judges/[name]/[promptId]`.

### `/runs/[id]/trials/[tid]` — trial detail (comprehensive view)

Two-column layout. Main column (left), sidebar (right).

Main column, top to bottom:

- Header: case, attempt, latency, tokens, cost (existing).
- **Input** — case input, presented prominently.
- **Agent output** — full text.
- **Tool calls** — table with expandable rows. Expanded row shows the parsed
  Tavily response: titles, snippets, URLs (parsed from the row's existing
  data — `tool_calls.result_json` if present, else fall back to extracting
  from the trace). Args also shown in the expanded row.
- **Verdicts**, grouped by judge. Each verdict block keeps current content
  (criterion text, score, confidence, reasoning, reviewer form) and adds a
  **"View judge prompt"** disclosure that renders the actual prompt sent
  (system + user with values substituted). Resolves the prompt by `judge_name
  + version` from the `prompts` table.
- **Trace** — raw, collapsible, kept at the bottom for completeness.

Sidebar:

- **Agent at-a-glance** — model, tool count, mini mermaid (4–5 nodes), link
  to `/agent`.
- **Reviewer notes (trial)** — moved here from the top of the page.
- **Quick links** — case page, run rollup.

### `/agent` — harness reference + inspector

Single page documenting the harness as it is right now. Static content, no
history widgets.

Sections:

- **Configuration** — current agent model (from a recent run row or a
  `harness_config` source of truth — see Open questions), tool list (names),
  cost row from `MODEL_COSTS`.
- **Inspector** — expandable disclosures:
  - **System prompt** — rendered text of the agent system prompt
  - **Tools** — one disclosure per tool, showing the tool's description /
    docstring and parameter schema
- **Graph** — full mermaid diagram of the LangChain `create_agent` graph
  (nodes `agent`, `tools`, the standard ReAct edges). Generated from
  `agent.get_graph()` if accessible, else committed as a static mermaid
  source file under `ui/lib/agent-graph.mmd`.
- **Recent runs using this agent** — small table linking back to `/runs`.

### `/judges` — hub

Keep existing layout: three P/R/F1 cards, recent judge-pr runs table. Card
links navigate to `/judges/[name]`.

### `/judges/[name]` — per-judge home (replaces `/prompts/[judge]`)

Sections:

- **Current configuration** — judge model, current `PROMPT_VERSION`,
  rendered prompt template (read-only).
- **Prompt version history** — table of all versions for this judge:
  version, first-used, last-used, # runs that used it, P/R/F1 for that
  version (computed by joining `judge_pr_runs` filtered to that prompt
  version). Each row links to `/judges/[name]/[promptId]`.
- **Gold-label stats for this judge** — pass / fail / auto counts (the
  per-judge stats currently on `/`'s gold-labels-by-judge table).

### `/judges/[name]/[promptId]` — historical prompt version

Existing diff view kept; navigation breadcrumb updated to `Judges → [name] →
v{version}`.

### `/` — home

Stays simple. Three count cards (Cases, Fixed outputs, Gold labels) link to
the new homes (Cases page, Cases page, Judges hub respectively). Add a
**latest run** card with the run id, agent model, pass rate, and a link to
`/runs/[id]`.

## Data sources

The redesign needs only a few new queries — no schema migration is expected.
Cases-detail merge re-uses existing `listFixedOutputs` and gold-label queries
filtered by `case_id`. Trial history per case is a join on
`trials.case_id`. Per-judge prompt history joins `prompts` and
`judge_pr_runs` on `judge_name + prompt_version`. Tavily search-result
parsing on the trial page reuses whatever is already persisted in
`tool_calls` (or, if needed, the trace text — to be confirmed during
implementation).

## Out of scope

- No design-system or aesthetic refresh. Tailwind classes and spacing stay
  as-is unless a layout change demands it.
- No changes to the run / trial pipeline, schema, or judge logic.
- No new authoring flows (e.g., creating a new case from the UI).

## Open questions

- **Source of truth for the Agent page configuration.** Current `agent.py`
  reads model from environment / call-site; the UI needs a deterministic way
  to know "the agent we'd run right now." Options: (a) introspect at request
  time by importing `agent` and rendering its config, (b) commit a small
  `harness_config.json` that `agent.py` and the UI both read. Decide during
  implementation.
- **Search-result parsing.** Confirm whether `tool_calls.result_json` is
  populated during eval runs. If not, the trial-page tool-call expansion
  parses from the trace; if so, it reads structured data directly. Worth
  one query against `evals.db` before writing the implementation plan.
