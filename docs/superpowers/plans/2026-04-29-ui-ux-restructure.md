# UI UX Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorient the eval UI around Cases / Runs / Agent / Judges, fold the golden dataset into Case detail, fold prompt history into per-judge pages, and make the trial detail the comprehensive single-execution surface.

**Architecture:** Pure Next.js 15 App Router restructure. No schema changes. New queries added to `ui/lib/queries.ts`; existing server actions reused (`updateCriterion`, `saveGoldLabel`, `updateFixedOutput`, `savePrompt`, `setActive`, `cloneAsNewVersion`). `/golden` and `/prompts` route trees are deleted. The `prompts` table the spec mentions is the existing `judge_prompts` table.

**Tech Stack:** Next.js 15 App Router · React 19 · TypeScript · Tailwind · better-sqlite3 against `evals.db`. No test framework in the UI; verification is visual via `npm run dev` (port 3030).

**Verification model.** The repo has no UI test framework. Each task ends with a manual verification step that hits a real URL with `npm run dev` and points at `evals.db`. Pure helpers (e.g. Tavily result parser) get small co-located TS unit tests run via `node --test` against compiled output, when introduced.

## Progress

Tasks 1–7 landed on branch `ui-ux-restructure` (commits d5ba332 → 7703656). Tasks 8–23 not started.

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Top nav | ✅ done | d5ba332 |
| 2 | `listCaseIndexRows` query | ✅ done | 804805e |
| 3 | `/cases` index page | ✅ done | fb42135 |
| 4 | `listTrialHistoryForCase` query | ✅ done | 841f103 |
| 5 | `/cases/[id]` server actions | ✅ done | 7969082 |
| 6 | `/cases/[id]` three-section page | ✅ done | 0761f4c |
| 7 | Delete `/golden` tree | ✅ done | 7703656 |
| 8 | Run rollup header summary | ✅ done | 60a4d78 |
| 9 | Run rollup judges-used in rail | ✅ done | 60a4d78 |
| 10 | Tavily parser + tests | ⬜ todo | — |
| 11 | Tool-call expandable row | ⬜ todo | — |
| 12 | Judge-prompt disclosure | ⬜ todo | — |
| 13 | Trial detail two-column | ⬜ todo | — |
| 14 | Move PR-run detail to /judges/runs | ⬜ todo | — |
| 15 | Per-judge home queries | ⬜ todo | — |
| 16 | Per-judge home actions | ⬜ todo | — |
| 17 | `/judges/[name]` page | ⬜ todo | — |
| 18 | `/judges/[name]/[promptId]` page | ⬜ todo | — |
| 19 | Delete `/prompts` tree | ⬜ todo | — |
| 20 | Agent harness static metadata | ⬜ todo | — |
| 21 | `/agent` page | ⬜ todo | — |
| 22 | Home page repoint + latest-run | ⬜ partial (count cards already repointed `/golden`→`/cases` in Task 7; latest-run card still pending) | — |
| 23 | Final smoke pass | ⬜ todo | — |

When picking up Task 22, note the `<Card href="/golden">` lines no longer exist — adjust the diff accordingly.

**Decisions resolved up front (from the spec's open questions):**

1. **Agent page config source of truth.** Read live values from the most recent `runs` row (`agent_model`, `agent_system_prompt`). Tool metadata and the LangGraph mermaid are committed as static files (`ui/lib/agent-info.ts`, `ui/lib/agent-graph.mmd`) — `agent.py` only declares one tool (`web_search`) with a fixed docstring, so duplicating that is cheaper than introspecting Python at request time.
2. **Tavily search-result parsing.** `tool_calls.result_json` does NOT exist in the schema (verified via `.schema tool_calls`). The `result` text column holds the rendered string `f"{title}\n{url}\n{content}"` joined by `\n\n` (see `agent.py:76-79`). Parse from that.
3. **`/judges/[id]` collision.** The existing route (per-PR-run detail keyed by `judge_pr_run_id`) is moved to `/judges/runs/[id]` so `/judges/[name]` is free.

**File structure (created / modified / deleted):**

Created
- `ui/lib/agent-info.ts` — static agent harness metadata (system prompt mirror, tool list, model default).
- `ui/lib/agent-graph.mmd` — static LangGraph mermaid source.
- `ui/lib/parse-tavily.ts` — pure parser for `tool_calls.result` text.
- `ui/lib/parse-tavily.test.mjs` — node:test for parser.
- `ui/app/agent/page.tsx` — agent harness reference page.
- `ui/app/judges/[name]/page.tsx` — per-judge home (replaces `/prompts/[judge]`).
- `ui/app/judges/[name]/[promptId]/page.tsx` — historical prompt version detail.
- `ui/app/judges/[name]/actions.ts` — server actions (moved from `app/prompts/actions.ts`, with revalidate paths updated).
- `ui/app/judges/runs/[id]/page.tsx` — relocation of existing PR-run detail.
- `ui/app/cases/[id]/golden-section.tsx` — collapsible fixed-output editor block (extracted client component).
- `ui/app/cases/[id]/actions.ts` — re-export of `updateCriterion` + `saveGoldLabel` + `updateFixedOutput` with `/cases/[id]` revalidation.
- `ui/app/runs/[id]/trials/[trialId]/tool-call-row.tsx` — client component for expandable tool-call row.
- `ui/app/runs/[id]/trials/[trialId]/judge-prompt-disclosure.tsx` — server-rendered disclosure showing rendered judge prompt.

Modified
- `ui/app/layout.tsx` — top nav.
- `ui/app/page.tsx` — three count cards re-pointed + new Latest Run card.
- `ui/app/cases/page.tsx` — table layout with new columns + filters.
- `ui/app/cases/[id]/page.tsx` — three-section stack.
- `ui/app/runs/[id]/page.tsx` — header summary line; Judges-used moves to right rail.
- `ui/app/runs/[id]/trials/[trialId]/page.tsx` — two-column layout, prominent input/output, sidebar.
- `ui/app/judges/page.tsx` — card links navigate to `/judges/[name]` (recent PR-runs table updated to `/judges/runs/[id]`).
- `ui/lib/queries.ts` — new queries listed per task.

Deleted
- `ui/app/golden/page.tsx`
- `ui/app/golden/[id]/page.tsx`
- `ui/app/golden/actions.ts`
- `ui/app/prompts/page.tsx`
- `ui/app/prompts/[judge]/page.tsx`
- `ui/app/prompts/[judge]/[id]/page.tsx`
- `ui/app/prompts/actions.ts`
- `ui/app/judges/[id]/page.tsx` (after relocation in Task 14)

Tasks are ordered so each one leaves the app runnable. The old routes are not deleted until their replacements work.

---

## Task 1: Top nav + new query helpers stub

**Files:**
- Modify: `ui/app/layout.tsx:11-20`
- Modify: `ui/lib/queries.ts` (add empty exports for queries that later tasks will fill)

- [x] **Step 1: Replace nav links**

In `ui/app/layout.tsx`, replace the `<nav>` block (lines 13-19) with:

```tsx
<nav className="flex gap-4 text-sm">
  <Link href="/cases" className="hover:underline">Cases</Link>
  <Link href="/runs" className="hover:underline">Runs</Link>
  <Link href="/agent" className="hover:underline">Agent</Link>
  <Link href="/judges" className="hover:underline">Judges</Link>
</nav>
```

- [x] **Step 2: Verify**

Run `cd ui && npm run dev` (port 3030). Visit `http://localhost:3030`. Expect: nav shows Cases · Runs · Agent · Judges. `/agent` will 404 — that's fine, it's built in Task 11. `/golden` and `/prompts` still load (deleted later).

- [x] **Step 3: Commit**

```bash
git add ui/app/layout.tsx
git commit -m "ui: switch top nav to cases/runs/agent/judges"
```

---

## Task 2: Cases-index queries

**Files:**
- Modify: `ui/lib/queries.ts` (append after `goldLabelStats` near end)

- [x] **Step 1: Add `caseIndexRows` query**

Append to `ui/lib/queries.ts`:

```ts
export type CaseIndexRow = {
  case_id: number;
  input: string;
  tags: string;
  criteria_count: number;
  fixed_output_count: number;
  correctness_pass: number;
  correctness_total: number;
  correctness_auto: number;
  faithfulness_pass: number;
  faithfulness_total: number;
  faithfulness_auto: number;
  needs_labels: number; // 1 if any case-scoped criterion has zero gold_labels
  last_trial_run_id: number | null;
  last_trial_id: number | null;
  last_trial_started: string | null;
  last_trial_pass: number | null;   // pass count across judges for that trial
  last_trial_total: number | null;
};

export function listCaseIndexRows(): CaseIndexRow[] {
  const rows = db()
    .prepare(
      `WITH lbl AS (
         SELECT cr.case_id, gl.judge_name,
                SUM(CASE WHEN gl.label = 1 THEN 1 ELSE 0 END) AS pass,
                SUM(CASE WHEN gl.label IS NOT NULL THEN 1 ELSE 0 END) AS total,
                SUM(CASE WHEN gl.labeler = 'auto-from-case-level' THEN 1 ELSE 0 END) AS auto
         FROM gold_labels gl
         JOIN criteria cr ON cr.criterion_id = gl.criterion_id
         GROUP BY cr.case_id, gl.judge_name
       ),
       last_trial AS (
         SELECT t.case_id, t.trial_id, t.run_id, t.created_at AS started
         FROM trials t
         JOIN (
           SELECT case_id, MAX(trial_id) AS max_id FROM trials GROUP BY case_id
         ) m ON m.case_id = t.case_id AND m.max_id = t.trial_id
       ),
       last_verdicts AS (
         SELECT v.trial_id,
                SUM(CASE WHEN v.score = 1 THEN 1 ELSE 0 END) AS pass,
                SUM(CASE WHEN v.score IS NOT NULL THEN 1 ELSE 0 END) AS total
         FROM criterion_verdicts v
         JOIN last_trial lt ON lt.trial_id = v.trial_id
         GROUP BY v.trial_id
       ),
       crit_counts AS (
         SELECT case_id, COUNT(*) AS n FROM criteria WHERE case_id IS NOT NULL GROUP BY case_id
       ),
       fo_counts AS (
         SELECT case_id, COUNT(*) AS n FROM fixed_outputs GROUP BY case_id
       ),
       missing AS (
         SELECT cr.case_id,
                SUM(CASE WHEN NOT EXISTS (
                       SELECT 1 FROM gold_labels gl WHERE gl.criterion_id = cr.criterion_id
                ) THEN 1 ELSE 0 END) AS missing_n
         FROM criteria cr
         WHERE cr.case_id IS NOT NULL
         GROUP BY cr.case_id
       )
       SELECT c.case_id, c.input, c.tags,
              COALESCE(cc.n, 0) AS criteria_count,
              COALESCE(fc.n, 0) AS fixed_output_count,
              COALESCE((SELECT pass FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_pass,
              COALESCE((SELECT total FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_total,
              COALESCE((SELECT auto FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_auto,
              COALESCE((SELECT pass FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_pass,
              COALESCE((SELECT total FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_total,
              COALESCE((SELECT auto FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_auto,
              CASE WHEN COALESCE(m.missing_n, 0) > 0 THEN 1 ELSE 0 END AS needs_labels,
              lt.run_id AS last_trial_run_id,
              lt.trial_id AS last_trial_id,
              lt.started AS last_trial_started,
              lv.pass AS last_trial_pass,
              lv.total AS last_trial_total
       FROM cases c
       LEFT JOIN crit_counts cc ON cc.case_id = c.case_id
       LEFT JOIN fo_counts fc ON fc.case_id = c.case_id
       LEFT JOIN missing m ON m.case_id = c.case_id
       LEFT JOIN last_trial lt ON lt.case_id = c.case_id
       LEFT JOIN last_verdicts lv ON lv.trial_id = lt.trial_id
       ORDER BY c.case_id`,
    )
    .all() as CaseIndexRow[];
  return rows;
}
```

- [x] **Step 2: Verify the query runs**

```bash
cd ui && npx tsc --noEmit
```

Expected: no type errors.

- [x] **Step 3: Commit**

```bash
git add ui/lib/queries.ts
git commit -m "ui: add listCaseIndexRows query for cases index page"
```

---

## Task 3: Cases index page

**Files:**
- Modify: `ui/app/cases/page.tsx` (full rewrite, ~80 lines)

- [x] **Step 1: Rewrite cases index**

Replace `ui/app/cases/page.tsx` with:

```tsx
import Link from "next/link";
import { listCaseIndexRows } from "@/lib/queries";

export const dynamic = "force-dynamic";

type FilterKey = "all" | "needs_labels" | "has_failures";

export default async function CasesIndex({
  searchParams,
}: {
  searchParams: Promise<{ filter?: FilterKey; tag?: string }>;
}) {
  const sp = await searchParams;
  const filter = (sp.filter ?? "all") as FilterKey;
  const tagFilter = sp.tag ?? "";

  const rows = listCaseIndexRows();
  const allTags = Array.from(
    new Set(
      rows.flatMap((r) => {
        try { return JSON.parse(r.tags) as string[]; } catch { return []; }
      }),
    ),
  ).sort();

  const filtered = rows.filter((r) => {
    if (filter === "needs_labels" && !r.needs_labels) return false;
    if (filter === "has_failures") {
      if (r.last_trial_pass == null || r.last_trial_total == null) return false;
      if (r.last_trial_pass === r.last_trial_total) return false;
    }
    if (tagFilter) {
      try { if (!(JSON.parse(r.tags) as string[]).includes(tagFilter)) return false; }
      catch { return false; }
    }
    return true;
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Cases</h1>

      <form className="flex flex-wrap gap-3 items-center text-sm">
        <label>
          Filter:
          <select name="filter" defaultValue={filter} className="ml-2 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
            <option value="all">All</option>
            <option value="needs_labels">Needs labels</option>
            <option value="has_failures">Has failures (last trial)</option>
          </select>
        </label>
        <label>
          Tag:
          <select name="tag" defaultValue={tagFilter} className="ml-2 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
            <option value="">(any)</option>
            {allTags.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        <button type="submit" className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Apply</button>
      </form>

      <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            <Th>Case input</Th>
            <Th># crit</Th>
            <Th># fixed</Th>
            <Th>Correctness gold</Th>
            <Th>Faithfulness gold</Th>
            <Th>Last trial</Th>
            <Th>Tags</Th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((r) => (
            <tr key={r.case_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
              <Td>
                <Link href={`/cases/${r.case_id}`} className="text-blue-600 hover:underline">
                  #{r.case_id} {r.input}
                </Link>
                {r.needs_labels === 1 && (
                  <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">needs labels</span>
                )}
              </Td>
              <Td>{r.criteria_count}</Td>
              <Td>{r.fixed_output_count}</Td>
              <Td>{r.correctness_total ? `${r.correctness_pass}/${r.correctness_total} (${r.correctness_auto} auto)` : "—"}</Td>
              <Td>{r.faithfulness_total ? `${r.faithfulness_pass}/${r.faithfulness_total} (${r.faithfulness_auto} auto)` : "—"}</Td>
              <Td className="text-xs">
                {r.last_trial_id != null ? (
                  <Link href={`/runs/${r.last_trial_run_id}/trials/${r.last_trial_id}`} className="text-blue-600 hover:underline">
                    run #{r.last_trial_run_id} · {r.last_trial_pass ?? 0}/{r.last_trial_total ?? 0}
                  </Link>
                ) : "—"}
              </Td>
              <Td className="text-xs text-zinc-500">{r.tags}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
```

- [x] **Step 2: Verify**

`cd ui && npm run dev`. Visit `http://localhost:3030/cases`. Expect: table with all cases, filters in URL (`?filter=needs_labels`), each row links to `/cases/[id]`.

- [x] **Step 3: Commit**

```bash
git add ui/app/cases/page.tsx
git commit -m "ui: rewrite cases index as table with gold-coverage columns"
```

---

## Task 4: Trial-history-per-case query

**Files:**
- Modify: `ui/lib/queries.ts` (append)

- [x] **Step 1: Add query**

Append to `ui/lib/queries.ts`:

```ts
export type CaseTrialHistoryRow = {
  trial_id: number;
  run_id: number;
  trial_idx: number;
  started_at: string;
  latency_ms: number | null;
  cost_usd: number | null;
  correctness_pass: number;
  correctness_total: number;
  faithfulness_pass: number;
  faithfulness_total: number;
  tool_use_pass: number;
  tool_use_total: number;
};

export function listTrialHistoryForCase(caseId: number): CaseTrialHistoryRow[] {
  return db()
    .prepare(
      `SELECT t.trial_id, t.run_id, t.trial_idx, t.created_at AS started_at,
              t.latency_ms, t.cost_usd,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score=1 THEN 1 ELSE 0 END) AS correctness_pass,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS correctness_total,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score=1 THEN 1 ELSE 0 END) AS faithfulness_pass,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS faithfulness_total,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score=1 THEN 1 ELSE 0 END) AS tool_use_pass,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS tool_use_total
       FROM trials t
       LEFT JOIN criterion_verdicts v ON v.trial_id = t.trial_id
       WHERE t.case_id = ?
       GROUP BY t.trial_id
       ORDER BY t.trial_id DESC`,
    )
    .all(caseId) as CaseTrialHistoryRow[];
}
```

- [x] **Step 2: Verify**

```bash
cd ui && npx tsc --noEmit
```

Expected: no errors.

- [x] **Step 3: Commit**

```bash
git add ui/lib/queries.ts
git commit -m "ui: add listTrialHistoryForCase query"
```

---

## Task 5: Cases detail — re-export server actions

**Files:**
- Create: `ui/app/cases/[id]/actions.ts`

- [x] **Step 1: Create actions.ts**

Create `ui/app/cases/[id]/actions.ts`:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { db, nowIso } from "@/lib/db";

export async function updateCriterion(formData: FormData) {
  const id = Number(formData.get("criterion_id"));
  const text = String(formData.get("text") ?? "").trim();
  if (!id || !text) throw new Error("missing criterion fields");
  db().prepare(`UPDATE criteria SET text = ? WHERE criterion_id = ?`).run(text, id);
  const caseId = formData.get("case_id");
  if (caseId) revalidatePath(`/cases/${caseId}`);
  revalidatePath(`/cases`);
}

export async function updateFixedOutput(formData: FormData) {
  const id = Number(formData.get("fixed_output_id"));
  const caseId = Number(formData.get("case_id"));
  const agentOutput = String(formData.get("agent_output") ?? "");
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id) throw new Error("missing fixed_output_id");
  db()
    .prepare(`UPDATE fixed_outputs SET agent_output = ?, notes = ? WHERE fixed_output_id = ?`)
    .run(agentOutput, notes, id);
  if (caseId) revalidatePath(`/cases/${caseId}`);
}

export async function saveGoldLabel(formData: FormData) {
  const fixedOutputId = Number(formData.get("fixed_output_id"));
  const criterionId = Number(formData.get("criterion_id"));
  const judgeName = String(formData.get("judge_name"));
  const labelStr = String(formData.get("label"));
  const labeler = String(formData.get("labeler") || "james").trim() || "james";
  const notes = String(formData.get("notes") || "") || null;
  const caseId = Number(formData.get("case_id"));
  if (!fixedOutputId || !criterionId || !judgeName) throw new Error("missing required fields");

  if (labelStr === "unset") {
    db()
      .prepare(`DELETE FROM gold_labels WHERE fixed_output_id = ? AND criterion_id = ? AND judge_name = ?`)
      .run(fixedOutputId, criterionId, judgeName);
  } else {
    const label = labelStr === "pass" ? 1 : 0;
    db()
      .prepare(
        `INSERT INTO gold_labels
           (criterion_id, fixed_output_id, judge_name, label, labeler, notes, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(criterion_id, fixed_output_id, judge_name)
         DO UPDATE SET label = excluded.label,
                       labeler = excluded.labeler,
                       notes = excluded.notes`,
      )
      .run(criterionId, fixedOutputId, judgeName, label, labeler, notes, nowIso());
  }

  if (caseId) revalidatePath(`/cases/${caseId}`);
}
```

- [x] **Step 2: Commit**

```bash
git add ui/app/cases/[id]/actions.ts
git commit -m "ui: copy gold-label and criterion actions to cases/[id]"
```

---

## Task 6: Cases detail — three-section page

**Files:**
- Modify: `ui/app/cases/[id]/page.tsx` (full rewrite)

- [x] **Step 1: Rewrite case detail**

Replace `ui/app/cases/[id]/page.tsx` with:

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getCase,
  listCriteriaForCase,
  listFixedOutputs,
  getGoldLabelsForFixedOutput,
  getFaithfulnessCriterion,
  listTrialHistoryForCase,
} from "@/lib/queries";
import { updateCriterion, updateFixedOutput, saveGoldLabel } from "./actions";

export const dynamic = "force-dynamic";

export default async function CaseDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = Number(id);
  const c = getCase(caseId);
  if (!c) notFound();
  const crits = listCriteriaForCase(caseId);
  const fixedOutputs = listFixedOutputs().filter((f) => f.case_id === caseId);
  const faithfulness = getFaithfulnessCriterion();
  const trials = listTrialHistoryForCase(caseId);

  return (
    <div className="space-y-8">
      <div>
        <Link href="/cases" className="text-sm text-blue-600 hover:underline">← Cases</Link>
        <h1 className="text-2xl font-semibold mt-1">Case #{c.case_id}</h1>
      </div>

      {/* 1. Definition */}
      <section className="space-y-3">
        <h2 className="font-semibold">Definition</h2>
        <div>
          <div className="text-xs text-zinc-500 mb-1">Input</div>
          <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded">{c.input}</p>
        </div>
        {c.expected && (
          <div>
            <div className="text-xs text-zinc-500 mb-1">Expected</div>
            <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded whitespace-pre-wrap">{c.expected}</p>
          </div>
        )}
        <p className="text-xs text-zinc-500">
          Editing a criterion invalidates downstream verdicts referencing it — bump <code>PROMPT_VERSION</code>
          in the corresponding judge if semantics change.
        </p>
        {crits.map((cr) => (
          <form
            key={cr.criterion_id}
            action={updateCriterion}
            className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2"
          >
            <input type="hidden" name="criterion_id" value={cr.criterion_id} />
            <input type="hidden" name="case_id" value={caseId} />
            <div className="text-xs text-zinc-500">
              {cr.judge_name} #{cr.idx} · id {cr.criterion_id}
            </div>
            <textarea
              name="text"
              defaultValue={cr.text}
              rows={2}
              className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
            />
            <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
              Save criterion
            </button>
          </form>
        ))}
      </section>

      {/* 2. Golden record */}
      <section className="space-y-3">
        <h2 className="font-semibold">Golden record ({fixedOutputs.length})</h2>
        {fixedOutputs.length === 0 && <p className="text-sm text-zinc-500">No fixed outputs.</p>}
        {fixedOutputs.map((fo) => {
          const labels = getGoldLabelsForFixedOutput(fo.fixed_output_id);
          const labelMap = new Map(labels.map((l) => [`${l.criterion_id}:${l.judge_name}`, l]));
          const correctnessCriteria = crits.filter((c) => c.judge_name === "correctness");
          return (
            <details key={fo.fixed_output_id} className="border border-zinc-200 dark:border-zinc-800 rounded">
              <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">
                Fixed output #{fo.fixed_output_id} · {fo.source ?? "—"} · {fo.created_at}
              </summary>
              <div className="p-3 space-y-4">
                <form action={updateFixedOutput} className="space-y-2">
                  <input type="hidden" name="fixed_output_id" value={fo.fixed_output_id} />
                  <input type="hidden" name="case_id" value={caseId} />
                  <label className="text-xs text-zinc-500">Agent output</label>
                  <textarea
                    name="agent_output"
                    defaultValue={fo.agent_output}
                    rows={10}
                    className="w-full p-3 font-mono text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
                  />
                  <textarea
                    name="notes"
                    defaultValue={fo.notes ?? ""}
                    placeholder="notes (optional)"
                    rows={2}
                    className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
                  />
                  <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                    Save output
                  </button>
                </form>

                <div className="space-y-2">
                  <h3 className="text-sm font-semibold">Correctness gold labels</h3>
                  {correctnessCriteria.map((cr) => {
                    const l = labelMap.get(`${cr.criterion_id}:correctness`);
                    return (
                      <LabelForm
                        key={cr.criterion_id}
                        fixedOutputId={fo.fixed_output_id}
                        caseId={caseId}
                        criterionId={cr.criterion_id}
                        judgeName="correctness"
                        criterionText={`#${cr.idx} ${cr.text}`}
                        currentLabel={l?.label}
                        currentLabeler={l?.labeler}
                        currentNotes={l?.notes ?? ""}
                      />
                    );
                  })}
                </div>

                {faithfulness && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold">Faithfulness gold label</h3>
                    <LabelForm
                      fixedOutputId={fo.fixed_output_id}
                      caseId={caseId}
                      criterionId={faithfulness.criterion_id}
                      judgeName="faithfulness"
                      criterionText={faithfulness.text}
                      currentLabel={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.label}
                      currentLabeler={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.labeler}
                      currentNotes={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.notes ?? ""}
                    />
                  </div>
                )}
              </div>
            </details>
          );
        })}
      </section>

      {/* 3. Trial history */}
      <section className="space-y-2">
        <h2 className="font-semibold">Trial history ({trials.length})</h2>
        {trials.length === 0 && <p className="text-sm text-zinc-500">No trials yet.</p>}
        {trials.length > 0 && (
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr>
                <Th>Run</Th><Th>Started</Th><Th>Attempt</Th>
                <Th>Correctness</Th><Th>Faithfulness</Th><Th>Tool use</Th>
                <Th>Latency</Th><Th>Cost</Th><Th>Trial</Th>
              </tr>
            </thead>
            <tbody>
              {trials.map((t) => (
                <tr key={t.trial_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td>#{t.run_id}</Td>
                  <Td className="text-xs">{t.started_at}</Td>
                  <Td>{t.trial_idx}</Td>
                  <Td>{t.correctness_total ? `${t.correctness_pass}/${t.correctness_total}` : "—"}</Td>
                  <Td>{t.faithfulness_total ? `${t.faithfulness_pass}/${t.faithfulness_total}` : "—"}</Td>
                  <Td>{t.tool_use_total ? `${t.tool_use_pass}/${t.tool_use_total}` : "—"}</Td>
                  <Td>{t.latency_ms != null ? `${t.latency_ms}ms` : "—"}</Td>
                  <Td>{t.cost_usd != null ? `$${t.cost_usd.toFixed(4)}` : "—"}</Td>
                  <Td>
                    <Link href={`/runs/${t.run_id}/trials/${t.trial_id}`} className="text-blue-600 hover:underline">
                      open →
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function LabelForm({
  fixedOutputId, caseId, criterionId, judgeName, criterionText,
  currentLabel, currentLabeler, currentNotes,
}: {
  fixedOutputId: number;
  caseId: number;
  criterionId: number;
  judgeName: string;
  criterionText: string;
  currentLabel: number | undefined;
  currentLabeler: string | undefined;
  currentNotes: string;
}) {
  const current = currentLabel === 1 ? "pass" : currentLabel === 0 ? "fail" : "unset";
  const isAuto = currentLabeler === "auto-from-case-level";
  return (
    <form action={saveGoldLabel} className="border border-zinc-200 dark:border-zinc-800 rounded p-2 space-y-2">
      <input type="hidden" name="fixed_output_id" value={fixedOutputId} />
      <input type="hidden" name="case_id" value={caseId} />
      <input type="hidden" name="criterion_id" value={criterionId} />
      <input type="hidden" name="judge_name" value={judgeName} />
      <p className="text-xs">{criterionText}</p>
      <div className="flex flex-wrap gap-2 items-center text-xs">
        <select name="label" defaultValue={current} className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
          <option value="pass">pass</option>
          <option value="fail">fail</option>
          <option value="unset">unset (delete)</option>
        </select>
        <input name="labeler" defaultValue={currentLabeler ?? "james"} className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950 w-32" />
        {isAuto && <span className="text-amber-600">⚠ auto</span>}
        <button className="px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
      </div>
      <textarea name="notes" defaultValue={currentNotes} placeholder="rationale" rows={1} className="w-full p-1 text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
    </form>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
```

- [x] **Step 2: Verify**

`cd ui && npm run dev`. Visit `/cases/1` (or any case ID with fixed outputs). Expect: three sections — Definition (with criteria editors), Golden record (collapsible per fixed output, with output editor + label forms), Trial history table. Test saving a criterion and a gold label.

- [x] **Step 3: Commit**

```bash
git add ui/app/cases/[id]/page.tsx
git commit -m "ui: case detail folds golden record and trial history"
```

---

## Task 7: Delete `/golden` routes

**Files:**
- Delete: `ui/app/golden/page.tsx`, `ui/app/golden/[id]/page.tsx`, `ui/app/golden/actions.ts`

- [x] **Step 1: Delete and re-point any callers**

```bash
rm ui/app/golden/page.tsx ui/app/golden/[id]/page.tsx ui/app/golden/actions.ts
rmdir ui/app/golden/[id] ui/app/golden
```

- [x] **Step 2: Update PR-run detail link to fixed_output**

In `ui/app/judges/[id]/page.tsx:90`, change `href={`/golden/${r.fixed_output_id}`}` to point at the case page:

```bash
grep -n "golden/" ui/app/judges/[id]/page.tsx
```

Then in `ui/app/judges/[id]/page.tsx`, replace the `<Link>` block at line 89-93 (`<Td>` for fixed_output) with:

```tsx
<Td>
  <Link href={`/cases/${r.case_id}`} className="text-blue-600 hover:underline">
    fo #{r.fixed_output_id}
  </Link>
</Td>
```

- [x] **Step 3: Search for any remaining /golden references**

```bash
grep -rn "/golden" ui/app ui/lib
```

Expected: no matches except nav (already changed). If any found in UI source, replace with `/cases` or `/cases/[id]`.

- [x] **Step 4: Type-check and verify**

```bash
cd ui && npx tsc --noEmit
npm run dev
```

Visit `/golden` — should 404. Visit `/cases/1` — still works. Visit `/judges/<some PR run id>` — fo links go to `/cases/[id]`.

- [x] **Step 5: Commit**

```bash
git add -A ui/app
git commit -m "ui: delete /golden route tree (folded into case detail)"
```

---

## Task 8: Run rollup — header summary line + agent_model in listing

**Files:**
- Modify: `ui/lib/queries.ts` (extend `getRun` or add `runSummary`)
- Modify: `ui/app/runs/[id]/page.tsx`

- [ ] **Step 1: Add summary query**

Append to `ui/lib/queries.ts`:

```ts
export type RunSummary = {
  run_id: number;
  agent_model: string;
  case_count: number;
  trial_count: number;
  total_cost: number;
  p50_latency_ms: number | null;
  p95_latency_ms: number | null;
  pass: number;
  total: number;
};

export function getRunSummary(runId: number): RunSummary | undefined {
  const base = db()
    .prepare(
      `SELECT r.run_id, r.agent_model,
              (SELECT COUNT(DISTINCT case_id) FROM trials WHERE run_id = r.run_id) AS case_count,
              (SELECT COUNT(*) FROM trials WHERE run_id = r.run_id) AS trial_count,
              COALESCE((SELECT SUM(cost_usd) FROM trials WHERE run_id = r.run_id), 0)
                + COALESCE((SELECT SUM(judge_cost_usd) FROM criterion_verdicts WHERE run_id = r.run_id), 0) AS total_cost,
              (SELECT SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) FROM criterion_verdicts WHERE run_id = r.run_id) AS pass,
              (SELECT SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) FROM criterion_verdicts WHERE run_id = r.run_id) AS total
       FROM runs r WHERE r.run_id = ?`,
    )
    .get(runId) as Omit<RunSummary, "p50_latency_ms" | "p95_latency_ms"> | undefined;
  if (!base) return undefined;
  const latencies = (
    db()
      .prepare(`SELECT latency_ms FROM trials WHERE run_id = ? AND latency_ms IS NOT NULL ORDER BY latency_ms`)
      .all(runId) as { latency_ms: number }[]
  ).map((r) => r.latency_ms);
  const pct = (p: number) =>
    latencies.length ? latencies[Math.min(latencies.length - 1, Math.floor(latencies.length * p))] : null;
  return { ...base, p50_latency_ms: pct(0.5), p95_latency_ms: pct(0.95) };
}
```

- [ ] **Step 2: Render summary line in run header**

In `ui/app/runs/[id]/page.tsx`, replace the import block top to include `getRunSummary`, and replace the `<p>` summary line at lines 36-39 with:

```tsx
{(() => {
  const s = getRunSummary(runId)!;
  const passPct = s.total ? Math.round((s.pass / s.total) * 100) : 0;
  return (
    <p className="text-sm text-zinc-500 mt-1">
      {s.agent_model} · {s.case_count} cases · {s.trial_count} trials · ${s.total_cost.toFixed(4)} ·
      {" "}p50 {s.p50_latency_ms ?? "—"}ms / p95 {s.p95_latency_ms ?? "—"}ms · pass {s.pass}/{s.total} ({passPct}%)
    </p>
  );
})()}
<p className="text-xs text-zinc-500 mt-1">
  started {run.started_at} · {run.trials_per_case} trials/case · config_hash <code>{run.config_hash}</code>
</p>
```

Update import at top of the file:

```tsx
import {
  caseRollupForRun,
  failureModeCountsForRun,
  getPromptIdByJudgeAndVersion,
  getRun,
  getRunSummary,
  listTrialsForRun,
  reviewedCountsForRun,
} from "@/lib/queries";
```

- [ ] **Step 3: Verify**

`cd ui && npm run dev`. Visit `/runs/<recent run id>`. Expect: header line shows `agent_model · N cases · M trials · $cost · p50/p95 · pass/total (pct%)`.

- [ ] **Step 4: Commit**

```bash
git add ui/lib/queries.ts ui/app/runs/[id]/page.tsx
git commit -m "ui: run header summary (cases/trials/cost/p50p95/pass)"
```

---

## Task 9: Run rollup — Judges-used moves to right rail

**Files:**
- Modify: `ui/app/runs/[id]/page.tsx`

- [ ] **Step 1: Move judges-used into the right aside**

In `ui/app/runs/[id]/page.tsx`, delete the `<section>` block with `<h2>Judges used</h2>` (currently lines 42-70). Then in the `<aside>` block (currently lines 133-147), prepend a Judges-used compact list, so the aside reads:

```tsx
<aside className="space-y-4">
  <section>
    <h2 className="font-semibold mb-2">Judges used</h2>
    <ul className="text-xs space-y-1">
      {Object.keys(judgeModels).map((j) => {
        const v = judgeVersions[j];
        const pid = v ? getPromptIdByJudgeAndVersion(j, v) : undefined;
        return (
          <li key={j} className="flex justify-between gap-2 border-b border-zinc-100 dark:border-zinc-800 py-1">
            <span>{j} · {judgeModels[j]}</span>
            {pid ? (
              <Link href={`/judges/${j}/${pid}`} className="text-blue-600 hover:underline font-mono">{v}</Link>
            ) : (
              <span className="font-mono">{v ?? "—"}</span>
            )}
          </li>
        );
      })}
    </ul>
  </section>
  <section>
    <h2 className="font-semibold mb-2">Failure modes</h2>
    {failureModes.length === 0 ? (
      <p className="text-xs text-zinc-500">No reviewed verdicts yet.</p>
    ) : (
      <ul className="text-sm space-y-1">
        {failureModes.map((fm) => (
          <li key={fm.failure_mode} className="flex justify-between gap-2 border-b border-zinc-100 dark:border-zinc-800 py-1">
            <span className="font-mono text-xs">{fm.failure_mode}</span>
            <span className="tabular-nums">{fm.n}</span>
          </li>
        ))}
      </ul>
    )}
  </section>
</aside>
```

Note: links go to `/judges/[name]/[promptId]` (not `/prompts/[name]/[promptId]`). The `/judges/[name]/[promptId]` route is built in Task 18; this link will 404 until then but the run page still renders.

- [ ] **Step 2: Verify**

`npm run dev`, visit `/runs/<id>`. Expect: judges-used now in right rail beside per-case rollup. Failure modes still below it.

- [ ] **Step 3: Commit**

```bash
git add ui/app/runs/[id]/page.tsx
git commit -m "ui: move judges-used block into run-detail right rail"
```

---

## Task 10: Tavily result parser + test

**Files:**
- Create: `ui/lib/parse-tavily.ts`
- Create: `ui/lib/parse-tavily.test.mjs`

- [ ] **Step 1: Create parser**

Create `ui/lib/parse-tavily.ts`:

```ts
export type TavilyResult = { title: string; url: string; content: string };

// Format produced by agent.py:web_search:
//   "{title}\n{url}\n{content}\n\n{title}\n{url}\n{content}\n\n..."
// Or the literal "No web results found."
export function parseTavilyResult(raw: string): TavilyResult[] {
  if (!raw || raw.trim() === "No web results found.") return [];
  const blocks = raw.split(/\n\n+/);
  const out: TavilyResult[] = [];
  for (const block of blocks) {
    const lines = block.split("\n");
    if (lines.length < 2) continue;
    const [title, url, ...rest] = lines;
    out.push({ title, url, content: rest.join("\n") });
  }
  return out;
}
```

- [ ] **Step 2: Create test**

Create `ui/lib/parse-tavily.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseTavilyResult } from "./parse-tavily.ts";

test("returns [] for empty / no results", () => {
  assert.deepEqual(parseTavilyResult(""), []);
  assert.deepEqual(parseTavilyResult("No web results found."), []);
});

test("parses two results separated by blank line", () => {
  const raw = "Title A\nhttps://a.example\nbody A line 1\nbody A line 2\n\nTitle B\nhttps://b.example\nbody B";
  const out = parseTavilyResult(raw);
  assert.equal(out.length, 2);
  assert.equal(out[0].title, "Title A");
  assert.equal(out[0].url, "https://a.example");
  assert.equal(out[0].content, "body A line 1\nbody A line 2");
  assert.equal(out[1].url, "https://b.example");
});

test("skips malformed blocks (single line)", () => {
  const out = parseTavilyResult("orphan line");
  assert.equal(out.length, 0);
});
```

- [ ] **Step 3: Run test**

`node --test --experimental-strip-types ui/lib/parse-tavily.test.mjs` (Node 22+ supports `--experimental-strip-types` for `.ts` imports). If the runtime can't strip TS, transpile via `npx tsc --module nodenext --target esnext --moduleResolution nodenext --noEmit false --outDir /tmp/parse-tavily ui/lib/parse-tavily.ts` and import the compiled `.js`.

Expected: 3 tests pass.

- [ ] **Step 4: Commit**

```bash
git add ui/lib/parse-tavily.ts ui/lib/parse-tavily.test.mjs
git commit -m "ui: add Tavily result parser with tests"
```

---

## Task 11: Trial detail — tool call expandable row

**Files:**
- Create: `ui/app/runs/[id]/trials/[trialId]/tool-call-row.tsx`

- [ ] **Step 1: Create client component**

Create `ui/app/runs/[id]/trials/[trialId]/tool-call-row.tsx`:

```tsx
"use client";

import { useState } from "react";
import { parseTavilyResult } from "@/lib/parse-tavily";

export function ToolCallRow({
  idx,
  toolName,
  args,
  result,
  latencyMs,
}: {
  idx: number;
  toolName: string;
  args: string;
  result: string;
  latencyMs: number | null;
}) {
  const [open, setOpen] = useState(false);
  const parsed = toolName === "web_search" ? parseTavilyResult(result) : [];

  return (
    <>
      <tr
        className="border-t border-zinc-200 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900"
        onClick={() => setOpen((o) => !o)}
      >
        <td className="px-3 py-2 w-8">{open ? "▾" : "▸"}</td>
        <td className="px-3 py-2">{idx + 1}</td>
        <td className="px-3 py-2">{toolName}</td>
        <td className="px-3 py-2 font-mono text-xs max-w-xl truncate" title={args}>{args}</td>
        <td className="px-3 py-2">{latencyMs != null ? `${latencyMs}ms` : "—"}</td>
      </tr>
      {open && (
        <tr className="border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
          <td colSpan={5} className="px-3 py-3">
            <div className="space-y-3">
              <div>
                <div className="text-xs text-zinc-500 mb-1">Args</div>
                <pre className="font-mono text-xs whitespace-pre-wrap">{args}</pre>
              </div>
              {parsed.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-xs text-zinc-500">Results ({parsed.length})</div>
                  {parsed.map((r, i) => (
                    <div key={i} className="border border-zinc-200 dark:border-zinc-800 rounded p-2 bg-white dark:bg-zinc-950">
                      <div className="text-sm font-medium">{r.title || "(no title)"}</div>
                      <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline break-all">{r.url}</a>
                      <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1 whitespace-pre-wrap line-clamp-6">{r.content}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Raw result</div>
                  <pre className="font-mono text-xs whitespace-pre-wrap max-h-96 overflow-auto">{result}</pre>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd ui && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add ui/app/runs/[id]/trials/[trialId]/tool-call-row.tsx
git commit -m "ui: add expandable ToolCallRow with Tavily result parsing"
```

---

## Task 12: Trial detail — judge-prompt disclosure

**Files:**
- Modify: `ui/lib/queries.ts` (add `resolveJudgePromptForRun`)
- Create: `ui/app/runs/[id]/trials/[trialId]/judge-prompt-disclosure.tsx`

- [ ] **Step 1: Add resolver query**

Append to `ui/lib/queries.ts`:

```ts
export function resolveJudgePrompt(judgeName: string, version: string): JudgePrompt | undefined {
  return db()
    .prepare(`SELECT * FROM judge_prompts WHERE judge_name = ? AND version = ?`)
    .get(judgeName, version) as JudgePrompt | undefined;
}
```

- [ ] **Step 2: Create disclosure component (server)**

Create `ui/app/runs/[id]/trials/[trialId]/judge-prompt-disclosure.tsx`:

```tsx
import { resolveJudgePrompt } from "@/lib/queries";

export function JudgePromptDisclosure({
  judgeName,
  version,
}: {
  judgeName: string;
  version: string | null;
}) {
  if (!version) return null;
  const prompt = resolveJudgePrompt(judgeName, version);
  if (!prompt) {
    return (
      <details className="mt-2 text-xs">
        <summary className="cursor-pointer text-blue-600 hover:underline">View judge prompt</summary>
        <p className="mt-1 text-zinc-500">Prompt {judgeName} v{version} not found in judge_prompts.</p>
      </details>
    );
  }
  return (
    <details className="mt-2 text-xs">
      <summary className="cursor-pointer text-blue-600 hover:underline">
        View judge prompt ({judgeName} <span className="font-mono">{version}</span>)
      </summary>
      <pre className="mt-2 p-3 rounded bg-zinc-100 dark:bg-zinc-900 whitespace-pre-wrap font-mono">{prompt.template}</pre>
      <p className="mt-1 text-zinc-500">
        Placeholders are filled at run-time by the judge with values like the agent input/output and evidence trace.
      </p>
    </details>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/lib/queries.ts ui/app/runs/[id]/trials/[trialId]/judge-prompt-disclosure.tsx
git commit -m "ui: add JudgePromptDisclosure for trial verdicts"
```

---

## Task 13: Trial detail — two-column layout, prominent input/output, sidebar

**Files:**
- Modify: `ui/app/runs/[id]/trials/[trialId]/page.tsx` (full rewrite)

- [ ] **Step 1: Rewrite trial detail**

Replace `ui/app/runs/[id]/trials/[trialId]/page.tsx` with:

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getRun,
  getTrace,
  getTrial,
  getToolCallsForTrial,
  getVerdictsForTrial,
} from "@/lib/queries";
import { TrialReview, VerdictReview } from "./review-forms";
import { ToolCallRow } from "./tool-call-row";
import { JudgePromptDisclosure } from "./judge-prompt-disclosure";

export const dynamic = "force-dynamic";

export default async function TrialDetail({
  params,
}: {
  params: Promise<{ id: string; trialId: string }>;
}) {
  const { id, trialId } = await params;
  const runId = Number(id);
  const tId = Number(trialId);
  const trial = getTrial(tId);
  if (!trial || trial.run_id !== runId) notFound();
  const run = getRun(runId)!;
  const verdicts = getVerdictsForTrial(tId);
  const toolCalls = getToolCallsForTrial(tId);
  const trace = trial.trace_id ? getTrace(trial.trace_id) : null;
  const traceBlocks = trace ? splitTrace(trace.content) : [];
  const judgeVersions = JSON.parse(run.judge_prompt_versions) as Record<string, string>;

  const byJudge = verdicts.reduce<Record<string, typeof verdicts>>((acc, v) => {
    (acc[v.judge_name] ??= []).push(v);
    return acc;
  }, {});

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
      <div className="space-y-6 min-w-0">
        <div>
          <Link href={`/runs/${runId}`} className="text-sm text-blue-600 hover:underline">← Run #{runId}</Link>
          <h1 className="text-2xl font-semibold mt-1">
            Trial {trial.trial_id} · case {trial.case_id} · attempt {trial.trial_idx}
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            {trial.latency_ms ?? "—"}ms · in {trial.tokens_in ?? "—"} / out {trial.tokens_out ?? "—"} tok ·
            {trial.cost_usd != null ? ` $${trial.cost_usd.toFixed(4)}` : " —"}
          </p>
        </div>

        <section className="space-y-2">
          <h2 className="font-semibold">Input</h2>
          <p className="text-base bg-zinc-100 dark:bg-zinc-900 p-3 rounded">{trial.case_input}</p>
        </section>

        <section className="space-y-2">
          <h2 className="font-semibold">Agent output</h2>
          <pre className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded whitespace-pre-wrap font-sans">
            {trial.output}
          </pre>
        </section>

        {toolCalls.length > 0 && (
          <section className="space-y-2">
            <h2 className="font-semibold">Tool calls ({toolCalls.length})</h2>
            <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
              <thead className="bg-zinc-100 dark:bg-zinc-900">
                <tr>
                  <Th></Th><Th>#</Th><Th>Tool</Th><Th>Args</Th><Th>Latency</Th>
                </tr>
              </thead>
              <tbody>
                {toolCalls.map((tc) => (
                  <ToolCallRow
                    key={tc.tool_call_id}
                    idx={tc.idx}
                    toolName={tc.tool_name}
                    args={tc.args}
                    result={tc.result}
                    latencyMs={tc.latency_ms}
                  />
                ))}
              </tbody>
            </table>
          </section>
        )}

        {Object.entries(byJudge).map(([judge, list]) => (
          <section key={judge} className="space-y-2">
            <h2 className="font-semibold capitalize">{judge} verdicts</h2>
            <div className="space-y-2">
              {list.map((v) => (
                <div key={v.verdict_id} className="border border-zinc-200 dark:border-zinc-800 rounded p-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="font-medium">
                      {judge === "faithfulness" ? "" : `#${v.criterion_idx} `}{v.criterion_text}
                    </div>
                    <div className="flex items-center gap-2">
                      <ScoreBadge score={v.score} />
                      <span className="text-xs text-zinc-500">conf {v.confidence}</span>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-2 whitespace-pre-wrap">{v.reasoning}</p>
                  <VerdictReview
                    verdictId={v.verdict_id}
                    runId={runId}
                    trialId={tId}
                    initialNotes={v.reviewer_notes}
                    initialMode={v.failure_mode}
                    reviewedAt={v.reviewed_at}
                  />
                </div>
              ))}
              <JudgePromptDisclosure judgeName={judge} version={judgeVersions[judge] ?? null} />
            </div>
          </section>
        ))}

        {trace && (
          <section className="space-y-2">
            <h2 className="font-semibold">Trace ({traceBlocks.length} block{traceBlocks.length === 1 ? "" : "s"})</h2>
            <div className="space-y-2">
              {traceBlocks.map((block, i) => (
                <details key={i} className="border border-zinc-200 dark:border-zinc-800 rounded">
                  <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">
                    {block.header}
                  </summary>
                  <pre className="text-xs p-3 whitespace-pre-wrap font-mono">{block.body}</pre>
                </details>
              ))}
            </div>
          </section>
        )}
      </div>

      <aside className="space-y-6">
        <section className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-1 text-xs">
          <h2 className="font-semibold text-sm">Agent</h2>
          <p>{run.agent_model}</p>
          <p className="text-zinc-500">1 tool · web_search</p>
          <pre className="font-mono text-[10px] mt-2 leading-tight bg-zinc-50 dark:bg-zinc-950 p-2 rounded">
{`graph TD
  user --> agent
  agent --> tools
  tools --> agent
  agent --> end`}
          </pre>
          <Link href="/agent" className="text-blue-600 hover:underline">View agent →</Link>
        </section>

        <section className="space-y-2">
          <h2 className="font-semibold text-sm">Reviewer notes (trial)</h2>
          <TrialReview trialId={tId} runId={runId} initialNotes={trial.reviewer_notes} />
        </section>

        <section className="space-y-1 text-sm">
          <h2 className="font-semibold">Quick links</h2>
          <Link href={`/cases/${trial.case_id}`} className="block text-blue-600 hover:underline">Case #{trial.case_id}</Link>
          <Link href={`/runs/${runId}`} className="block text-blue-600 hover:underline">Run #{runId}</Link>
        </section>
      </aside>
    </div>
  );
}

function splitTrace(content: string): { header: string; body: string }[] {
  const parts = content.split(/(?=^\[search \d+\])/m);
  return parts.filter((p) => p.trim()).map((p) => {
    const idx = p.indexOf("\n");
    if (idx === -1) return { header: p.slice(0, 80), body: p };
    return { header: p.slice(0, idx), body: p.slice(idx + 1) };
  });
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === 1) return <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-800">pass</span>;
  if (score === 0) return <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800">fail</span>;
  return <span className="text-xs px-2 py-0.5 rounded bg-zinc-200 text-zinc-700">unknown</span>;
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
```

- [ ] **Step 2: Verify**

`npm run dev`. Visit `/runs/<id>/trials/<id>` for a trial that has tool_calls. Expect: two-column layout, expandable tool-call rows showing parsed Tavily titles/URLs, "View judge prompt" disclosure under each judge group, sidebar with agent at-a-glance + reviewer notes + quick links.

- [ ] **Step 3: Commit**

```bash
git add ui/app/runs/[id]/trials/[trialId]/page.tsx
git commit -m "ui: trial detail two-column layout with prominent input/output and sidebar"
```

---

## Task 14: Move PR-run detail to /judges/runs/[id]

**Files:**
- Create: `ui/app/judges/runs/[id]/page.tsx` (move from `ui/app/judges/[id]/page.tsx`)
- Delete: `ui/app/judges/[id]/page.tsx`
- Modify: `ui/app/judges/page.tsx` (update both card and table links)

- [ ] **Step 1: Move file**

```bash
mkdir -p ui/app/judges/runs/[id]
git mv ui/app/judges/[id]/page.tsx ui/app/judges/runs/[id]/page.tsx
rmdir ui/app/judges/[id] 2>/dev/null || true
```

- [ ] **Step 2: Update back-link inside the moved file**

In `ui/app/judges/runs/[id]/page.tsx`, change `<Link href="/judges" className="text-sm text-blue-600 hover:underline">← Judge Health</Link>` to `<Link href="/judges" className="text-sm text-blue-600 hover:underline">← Judges</Link>`.

- [ ] **Step 3: Update links in `ui/app/judges/page.tsx`**

In `ui/app/judges/page.tsx`:

- Card link (line 38): change `href={`/judges/${r.judge_pr_run_id}`}` to `href={`/judges/${j}`}` (cards now link to per-judge home, built next task).
- Table row link (line 73): change `href={`/judges/${r.judge_pr_run_id}`}` to `href={`/judges/runs/${r.judge_pr_run_id}`}`.

Also change the `<h1>` text from `Judge Health` to `Judges` and the description's `Judge Health` mentions if any.

- [ ] **Step 4: Verify**

`npm run dev`. Visit `/judges` → cards link to `/judges/correctness` (404 — built next task). Recent runs table links to `/judges/runs/<id>` and that page renders the existing PR-run detail.

- [ ] **Step 5: Commit**

```bash
git add -A ui/app/judges
git commit -m "ui: move PR-run detail to /judges/runs/[id]"
```

---

## Task 15: Per-judge home queries

**Files:**
- Modify: `ui/lib/queries.ts` (append)

- [ ] **Step 1: Add per-judge prompt history query**

Append to `ui/lib/queries.ts`:

```ts
export type JudgePromptHistoryRow = {
  judge_prompt_id: number;
  judge_name: string;
  version: string;
  is_active: number;
  template: string;
  notes: string | null;
  updated_at: string;
  used_by_runs: number;
  first_used: string | null;
  last_used: string | null;
  precision_pct: number | null;
  recall_pct: number | null;
  f1_pct: number | null;
};

export function listJudgePromptHistory(judgeName: string): JudgePromptHistoryRow[] {
  const prompts = listPromptsForJudge(judgeName);
  return prompts.map((p) => {
    const runs = db()
      .prepare(`SELECT started_at FROM runs ORDER BY started_at`)
      .all() as { started_at: string }[];
    let first: string | null = null;
    let last: string | null = null;
    let usedBy = 0;
    for (const r of runs) {
      // re-fetch judge_prompt_versions for each row to filter
    }
    // efficient: filter rows by JSON_EXTRACT
    const matching = db()
      .prepare(
        `SELECT started_at FROM runs
         WHERE json_extract(judge_prompt_versions, '$.' || ?) = ?
         ORDER BY started_at`,
      )
      .all(judgeName, p.version) as { started_at: string }[];
    if (matching.length) {
      first = matching[0].started_at;
      last = matching[matching.length - 1].started_at;
      usedBy = matching.length;
    }
    const pr = db()
      .prepare(
        `SELECT precision_pct, recall_pct, f1_pct
         FROM judge_pr_runs
         WHERE judge_name = ? AND prompt_version = ?
         ORDER BY started_at DESC LIMIT 1`,
      )
      .get(judgeName, p.version) as
      | { precision_pct: number; recall_pct: number; f1_pct: number }
      | undefined;
    return {
      judge_prompt_id: p.judge_prompt_id,
      judge_name: p.judge_name,
      version: p.version,
      is_active: p.is_active,
      template: p.template,
      notes: p.notes,
      updated_at: p.updated_at,
      used_by_runs: usedBy,
      first_used: first,
      last_used: last,
      precision_pct: pr?.precision_pct ?? null,
      recall_pct: pr?.recall_pct ?? null,
      f1_pct: pr?.f1_pct ?? null,
    };
  });
}

export function goldLabelStatsForJudge(judgeName: string): GoldLabelStat | undefined {
  return db()
    .prepare(
      `SELECT judge_name,
              COUNT(*) AS total,
              SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) AS pass,
              SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) AS fail,
              SUM(CASE WHEN labeler = 'auto-from-case-level' THEN 0 ELSE 1 END) AS hand,
              SUM(CASE WHEN labeler = 'auto-from-case-level' THEN 1 ELSE 0 END) AS auto
       FROM gold_labels WHERE judge_name = ?
       GROUP BY judge_name`,
    )
    .get(judgeName) as GoldLabelStat | undefined;
}
```

Remove the dead `for (const r of runs)` loop (it's a leftover scaffold) — the function should look like:

```ts
export function listJudgePromptHistory(judgeName: string): JudgePromptHistoryRow[] {
  const prompts = listPromptsForJudge(judgeName);
  return prompts.map((p) => {
    const matching = db()
      .prepare(
        `SELECT started_at FROM runs
         WHERE json_extract(judge_prompt_versions, '$.' || ?) = ?
         ORDER BY started_at`,
      )
      .all(judgeName, p.version) as { started_at: string }[];
    const first = matching.length ? matching[0].started_at : null;
    const last = matching.length ? matching[matching.length - 1].started_at : null;
    const usedBy = matching.length;
    const pr = db()
      .prepare(
        `SELECT precision_pct, recall_pct, f1_pct
         FROM judge_pr_runs
         WHERE judge_name = ? AND prompt_version = ?
         ORDER BY started_at DESC LIMIT 1`,
      )
      .get(judgeName, p.version) as
      | { precision_pct: number; recall_pct: number; f1_pct: number }
      | undefined;
    return {
      judge_prompt_id: p.judge_prompt_id,
      judge_name: p.judge_name,
      version: p.version,
      is_active: p.is_active,
      template: p.template,
      notes: p.notes,
      updated_at: p.updated_at,
      used_by_runs: usedBy,
      first_used: first,
      last_used: last,
      precision_pct: pr?.precision_pct ?? null,
      recall_pct: pr?.recall_pct ?? null,
      f1_pct: pr?.f1_pct ?? null,
    };
  });
}
```

- [ ] **Step 2: Type-check**

```bash
cd ui && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add ui/lib/queries.ts
git commit -m "ui: add per-judge prompt-history and gold-stat queries"
```

---

## Task 16: Per-judge home page actions

**Files:**
- Create: `ui/app/judges/[name]/actions.ts`

- [ ] **Step 1: Create actions**

Create `ui/app/judges/[name]/actions.ts`:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { db, nowIso } from "@/lib/db";

export async function savePrompt(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  const template = String(formData.get("template") ?? "");
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id || !template.trim()) throw new Error("missing required fields");

  db()
    .prepare(`UPDATE judge_prompts SET template = ?, notes = ?, updated_at = ? WHERE judge_prompt_id = ?`)
    .run(template, notes, nowIso(), id);

  const row = db()
    .prepare(`SELECT judge_name FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string } | undefined;
  if (row) {
    revalidatePath(`/judges/${row.judge_name}`);
    revalidatePath(`/judges/${row.judge_name}/${id}`);
  }
}

export async function setActive(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  if (!id) throw new Error("missing id");
  const row = db()
    .prepare(`SELECT judge_name FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string } | undefined;
  if (!row) throw new Error("not found");

  const tx = db().transaction(() => {
    db().prepare(`UPDATE judge_prompts SET is_active = 0 WHERE judge_name = ?`).run(row.judge_name);
    db().prepare(`UPDATE judge_prompts SET is_active = 1, updated_at = ? WHERE judge_prompt_id = ?`).run(nowIso(), id);
  });
  tx();

  revalidatePath(`/judges/${row.judge_name}`);
}

export async function cloneAsNewVersion(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  const newVersion = String(formData.get("new_version") ?? "").trim();
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id || !newVersion) throw new Error("missing fields");

  const src = db()
    .prepare(`SELECT judge_name, template FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string; template: string } | undefined;
  if (!src) throw new Error("source prompt not found");

  const ts = nowIso();
  db()
    .prepare(
      `INSERT INTO judge_prompts
         (judge_name, version, template, notes, is_active, created_at, updated_at)
       VALUES (?, ?, ?, ?, 0, ?, ?)`,
    )
    .run(src.judge_name, newVersion, src.template, notes, ts, ts);

  revalidatePath(`/judges/${src.judge_name}`);
}
```

- [ ] **Step 2: Commit**

```bash
git add ui/app/judges/[name]/actions.ts
git commit -m "ui: add prompt edit/activate/clone actions for per-judge route"
```

---

## Task 17: Per-judge home page

**Files:**
- Create: `ui/app/judges/[name]/page.tsx`

- [ ] **Step 1: Create page**

Create `ui/app/judges/[name]/page.tsx`:

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  activePromptByJudge,
  goldLabelStatsForJudge,
  listJudgePromptHistory,
  PLACEHOLDERS,
} from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function PerJudgeHome({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  const history = listJudgePromptHistory(name);
  if (history.length === 0) notFound();
  const active = activePromptByJudge()[name];
  const stats = goldLabelStatsForJudge(name);
  const placeholders = PLACEHOLDERS[name] ?? [];

  return (
    <div className="space-y-8">
      <div>
        <Link href="/judges" className="text-sm text-blue-600 hover:underline">← Judges</Link>
        <h1 className="text-2xl font-semibold mt-1">{name}</h1>
      </div>

      <section className="space-y-3">
        <h2 className="font-semibold">Current configuration</h2>
        {active ? (
          <div className="space-y-2 text-sm">
            <p><strong>Active version:</strong> <span className="font-mono">{active.version}</span></p>
            {placeholders.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {placeholders.map((p) => (
                  <code key={p} className="px-2 py-1 bg-zinc-100 dark:bg-zinc-900 rounded text-xs">{`{${p}}`}</code>
                ))}
              </div>
            )}
            <pre className="text-xs font-mono whitespace-pre-wrap p-3 rounded bg-zinc-100 dark:bg-zinc-900 max-h-96 overflow-auto">{active.template}</pre>
          </div>
        ) : (
          <p className="text-sm text-zinc-500">No active prompt for this judge.</p>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Prompt version history</h2>
        <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr>
              <Th>Version</Th><Th>Active</Th><Th>First used</Th><Th>Last used</Th>
              <Th># runs</Th><Th>P</Th><Th>R</Th><Th>F1</Th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.judge_prompt_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <Td>
                  <Link href={`/judges/${name}/${h.judge_prompt_id}`} className="text-blue-600 hover:underline font-mono">
                    {h.version}
                  </Link>
                </Td>
                <Td>{h.is_active ? <span className="text-green-600">●</span> : "—"}</Td>
                <Td className="text-xs">{h.first_used ?? "—"}</Td>
                <Td className="text-xs">{h.last_used ?? "—"}</Td>
                <Td>{h.used_by_runs}</Td>
                <Td>{h.precision_pct != null ? `${(h.precision_pct * 100).toFixed(0)}%` : "—"}</Td>
                <Td>{h.recall_pct != null ? `${(h.recall_pct * 100).toFixed(0)}%` : "—"}</Td>
                <Td className="font-medium">{h.f1_pct != null ? `${(h.f1_pct * 100).toFixed(0)}%` : "—"}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Gold-label stats</h2>
        {stats ? (
          <table className="text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr><Th>Total</Th><Th>Pass</Th><Th>Fail</Th><Th>Hand</Th><Th>Auto</Th></tr>
            </thead>
            <tbody>
              <tr className="border-t border-zinc-200 dark:border-zinc-800">
                <Td>{stats.total}</Td><Td>{stats.pass}</Td><Td>{stats.fail}</Td>
                <Td>{stats.hand}</Td><Td>{stats.auto}</Td>
              </tr>
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-zinc-500">No gold labels yet.</p>
        )}
      </section>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
```

- [ ] **Step 2: Verify**

`npm run dev`. Visit `/judges/correctness`. Expect: active prompt rendered, version table with first/last used + P/R/F1 (latest PR-run per version), gold stats row.

- [ ] **Step 3: Commit**

```bash
git add ui/app/judges/[name]/page.tsx
git commit -m "ui: add /judges/[name] per-judge home"
```

---

## Task 18: Historical prompt version detail

**Files:**
- Create: `ui/app/judges/[name]/[promptId]/page.tsx`

- [ ] **Step 1: Create page**

Create `ui/app/judges/[name]/[promptId]/page.tsx`:

```tsx
import Link from "next/link";
import { notFound } from "next/navigation";
import { getPrompt, PLACEHOLDERS, promptUsedByRunCount } from "@/lib/queries";
import { cloneAsNewVersion, savePrompt, setActive } from "../actions";

export const dynamic = "force-dynamic";

export default async function PromptVersionDetail({
  params,
}: {
  params: Promise<{ name: string; promptId: string }>;
}) {
  const { name, promptId } = await params;
  const id = Number(promptId);
  const p = getPrompt(id);
  if (!p || p.judge_name !== name) notFound();
  const placeholders = PLACEHOLDERS[name] ?? [];
  const usedBy = promptUsedByRunCount(name, p.version);

  return (
    <div className="space-y-6">
      <div className="text-sm text-blue-600">
        <Link href="/judges" className="hover:underline">Judges</Link>
        <span className="mx-1 text-zinc-400">→</span>
        <Link href={`/judges/${name}`} className="hover:underline">{name}</Link>
        <span className="mx-1 text-zinc-400">→</span>
        <span className="font-mono">v{p.version.replace(/^v/, "")}</span>
      </div>
      <h1 className="text-2xl font-semibold">
        <span className="font-mono">{p.version}</span>
        {p.is_active ? <span className="ml-2 text-sm text-green-600">● active</span> : null}
      </h1>
      <p className="text-sm text-zinc-500">
        Used by {usedBy} run{usedBy === 1 ? "" : "s"} · updated {p.updated_at}
      </p>
      {usedBy > 0 && (
        <p className="text-xs text-amber-600">
          ⚠ This version has been used by stored runs. Editing will retroactively change what those runs claim
          to have used. Consider "Clone to new version" instead.
        </p>
      )}

      {placeholders.length > 0 && (
        <section className="text-sm">
          <div className="text-zinc-500 mb-1">Placeholders available:</div>
          <div className="flex flex-wrap gap-2">
            {placeholders.map((ph) => (
              <code key={ph} className="px-2 py-1 bg-zinc-100 dark:bg-zinc-900 rounded text-xs">{`{${ph}}`}</code>
            ))}
          </div>
        </section>
      )}

      <section>
        <form action={savePrompt} className="space-y-2">
          <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
          <label className="block text-sm font-semibold">Template</label>
          <textarea name="template" defaultValue={p.template} rows={24}
            className="w-full p-3 font-mono text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <label className="block text-sm font-semibold mt-2">Notes</label>
          <textarea name="notes" defaultValue={p.notes ?? ""} rows={2}
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            Save edits
          </button>
        </form>
      </section>

      <section className="grid grid-cols-2 gap-4">
        {!p.is_active && (
          <form action={setActive} className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2">
            <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
            <h3 className="font-semibold text-sm">Activate</h3>
            <p className="text-xs text-zinc-500">Mark this version active.</p>
            <button className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700">Set active</button>
          </form>
        )}
        <form action={cloneAsNewVersion} className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2">
          <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
          <h3 className="font-semibold text-sm">Clone to new version</h3>
          <input name="new_version" placeholder="e.g. v2" required
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <input name="notes" placeholder="what changed"
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <button className="px-3 py-1.5 text-sm bg-zinc-700 text-white rounded hover:bg-zinc-800">Create new version</button>
        </form>
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Verify**

`npm run dev`. Visit `/judges/correctness/<id>` for any judge_prompt_id. Expect: breadcrumb `Judges → correctness → vN`, editable template, activate (if not active), clone form. Trial-detail's "View judge prompt" link from Task 9's run-rollup link should now resolve.

- [ ] **Step 3: Commit**

```bash
git add ui/app/judges/[name]/[promptId]/page.tsx
git commit -m "ui: add /judges/[name]/[promptId] historical version page"
```

---

## Task 19: Delete /prompts route tree

**Files:**
- Delete: `ui/app/prompts/**`

- [ ] **Step 1: Verify nothing else imports from `app/prompts/`**

```bash
grep -rn "app/prompts" ui/app ui/lib
```

Expected: no matches in non-prompts files.

- [ ] **Step 2: Delete**

```bash
rm -r ui/app/prompts
```

- [ ] **Step 3: Type-check + smoke test**

```bash
cd ui && npx tsc --noEmit
npm run dev
```

Visit `/prompts` → 404. Visit `/judges/correctness` → loads. Visit `/runs/<id>` → judges-used links go to `/judges/<name>/<id>` and resolve.

- [ ] **Step 4: Commit**

```bash
git add -A ui/app
git commit -m "ui: delete /prompts route tree (folded into /judges/[name])"
```

---

## Task 20: Agent harness static metadata

**Files:**
- Create: `ui/lib/agent-info.ts`
- Create: `ui/lib/agent-graph.mmd`

- [ ] **Step 1: Create agent-info.ts**

The system prompt and tool description below are mirrored verbatim from `agent.py:14-20` and `agent.py:55-56`. If `agent.py` changes, update this file.

Create `ui/lib/agent-info.ts`:

```ts
export const AGENT_SYSTEM_PROMPT = `You answer general questions using Tavily web search from public internet sources.
            You should cite your sources and include excerpts from cited sources to support and augment answers provided.
            The user needs to trust your answers and feel as though you have accurately researched their topic - so ensure
            you provide evidence from unbiased sources and avoid relying on your internal knowledge unless you are supremely confident.
            When comparing data, ensure you state any caveats or assumptions.
            Be precise and thorough in your responses.
            `;

export type AgentTool = {
  name: string;
  description: string;
  parameters: { name: string; type: string; description: string }[];
};

export const AGENT_TOOLS: AgentTool[] = [
  {
    name: "web_search",
    description: "Search the public web via Tavily and return top results with extracted page content.",
    parameters: [{ name: "query", type: "string", description: "The search query string." }],
  },
];

export const AGENT_DEFAULT_MODEL = "openai:gpt-5.4-mini";
```

- [ ] **Step 2: Create mermaid graph**

Create `ui/lib/agent-graph.mmd`:

```
graph TD
  start([__start__]) --> agent
  agent -->|tool_calls present| tools
  tools --> agent
  agent -->|no tool_calls| end_node([__end__])
```

- [ ] **Step 3: Commit**

```bash
git add ui/lib/agent-info.ts ui/lib/agent-graph.mmd
git commit -m "ui: add static agent harness metadata + langgraph mermaid"
```

---

## Task 21: Agent page

**Files:**
- Modify: `ui/lib/queries.ts` (append `mostRecentRun`, `recentRunsByModel`)
- Create: `ui/app/agent/page.tsx`

- [ ] **Step 1: Add queries**

Append to `ui/lib/queries.ts`:

```ts
export function mostRecentRun(): Run | undefined {
  return db().prepare(`SELECT * FROM runs ORDER BY started_at DESC LIMIT 1`).get() as Run | undefined;
}

export function recentRunsByModel(agentModel: string, limit = 10): Run[] {
  return db()
    .prepare(`SELECT * FROM runs WHERE agent_model = ? ORDER BY started_at DESC LIMIT ?`)
    .all(agentModel, limit) as Run[];
}
```

- [ ] **Step 2: Create agent page**

Create `ui/app/agent/page.tsx`:

```tsx
import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import { AGENT_DEFAULT_MODEL, AGENT_SYSTEM_PROMPT, AGENT_TOOLS } from "@/lib/agent-info";
import { mostRecentRun, recentRunsByModel } from "@/lib/queries";

export const dynamic = "force-dynamic";

const MODEL_COSTS: Record<string, [number, number]> = {
  // Mirror of costs.py MODEL_COSTS (per 1k tokens). Update if costs.py changes.
  "gpt-5.4-mini": [0.0, 0.0],
};

export default function AgentPage() {
  const latest = mostRecentRun();
  const liveModel = latest?.agent_model ?? AGENT_DEFAULT_MODEL;
  const liveSystemPrompt = latest?.agent_system_prompt ?? AGENT_SYSTEM_PROMPT;
  const recentRuns = latest ? recentRunsByModel(latest.agent_model, 10) : [];
  const graphPath = path.resolve(process.cwd(), "lib", "agent-graph.mmd");
  const graph = fs.existsSync(graphPath) ? fs.readFileSync(graphPath, "utf-8") : "";
  const cost = MODEL_COSTS[liveModel.replace(/^openai:/, "")];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Agent harness</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Tavily-search LangChain agent. Live values come from the most recent run row;
          static metadata (tools, graph) is mirrored from <code>agent.py</code>.
        </p>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Configuration</h2>
        <table className="text-sm border border-zinc-200 dark:border-zinc-800">
          <tbody>
            <tr className="border-b border-zinc-200 dark:border-zinc-800"><Td className="font-medium">Model</Td><Td>{liveModel}</Td></tr>
            <tr className="border-b border-zinc-200 dark:border-zinc-800"><Td className="font-medium">Tools</Td><Td>{AGENT_TOOLS.map((t) => t.name).join(", ")}</Td></tr>
            <tr><Td className="font-medium">Cost / 1k tok (in/out)</Td><Td>{cost ? `$${cost[0]} / $${cost[1]}` : "—"}</Td></tr>
          </tbody>
        </table>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Inspector</h2>
        <details className="border border-zinc-200 dark:border-zinc-800 rounded">
          <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">System prompt</summary>
          <pre className="text-xs p-3 whitespace-pre-wrap font-mono">{liveSystemPrompt}</pre>
        </details>
        {AGENT_TOOLS.map((t) => (
          <details key={t.name} className="border border-zinc-200 dark:border-zinc-800 rounded">
            <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">Tool: {t.name}</summary>
            <div className="p-3 space-y-2 text-sm">
              <p>{t.description}</p>
              <div>
                <div className="text-xs text-zinc-500">Parameters</div>
                <ul className="list-disc list-inside text-xs">
                  {t.parameters.map((p) => (
                    <li key={p.name}><code>{p.name}</code> ({p.type}) — {p.description}</li>
                  ))}
                </ul>
              </div>
            </div>
          </details>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Graph</h2>
        <pre className="text-xs p-3 rounded bg-zinc-100 dark:bg-zinc-900 font-mono whitespace-pre-wrap">{graph || "(graph file missing)"}</pre>
        <p className="text-xs text-zinc-500">
          Source: <code>ui/lib/agent-graph.mmd</code>. Paste into a mermaid renderer to view.
        </p>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Recent runs using this agent ({liveModel})</h2>
        {recentRuns.length === 0 ? (
          <p className="text-sm text-zinc-500">No runs.</p>
        ) : (
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr><Th>Run</Th><Th>Started</Th><Th>Tag</Th><Th>Hash</Th></tr>
            </thead>
            <tbody>
              {recentRuns.map((r) => (
                <tr key={r.run_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td><Link href={`/runs/${r.run_id}`} className="text-blue-600 hover:underline">#{r.run_id}</Link></Td>
                  <Td className="text-xs">{r.started_at}</Td>
                  <Td className="text-xs">{r.tag ?? "—"}</Td>
                  <Td className="font-mono text-xs">{r.config_hash.slice(0, 8)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
```

- [ ] **Step 3: Verify**

`npm run dev`. Visit `/agent`. Expect: configuration table (model from latest run), inspector disclosures (system prompt + web_search tool), mermaid source block, recent-runs table.

- [ ] **Step 4: Commit**

```bash
git add ui/lib/queries.ts ui/app/agent/page.tsx
git commit -m "ui: add /agent harness reference page"
```

---

## Task 22: Home page — count cards repointed + latest-run card

**Files:**
- Modify: `ui/app/page.tsx`

- [ ] **Step 1: Rewrite home**

Replace `ui/app/page.tsx` with:

```tsx
import Link from "next/link";
import { goldLabelStats, listCases, listFixedOutputs, mostRecentRun, getRunSummary } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default function Home() {
  const cases = listCases();
  const outputs = listFixedOutputs();
  const stats = goldLabelStats();
  const latest = mostRecentRun();
  const summary = latest ? getRunSummary(latest.run_id) : undefined;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Agent Eval Harness</h1>

      <div className="grid grid-cols-3 gap-4">
        <Card title="Cases" value={cases.length} href="/cases" />
        <Card title="Fixed outputs" value={outputs.length} href="/cases" />
        <Card title="Gold labels" value={stats.reduce((a, s) => a + s.total, 0)} href="/judges" />
      </div>

      {latest && summary && (
        <section className="border border-zinc-200 dark:border-zinc-800 rounded p-4 space-y-1">
          <div className="flex items-baseline justify-between">
            <h2 className="font-semibold">Latest run</h2>
            <Link href={`/runs/${latest.run_id}`} className="text-sm text-blue-600 hover:underline">
              Run #{latest.run_id} →
            </Link>
          </div>
          <p className="text-sm text-zinc-500">
            {latest.agent_model} · started {latest.started_at} · pass {summary.pass}/{summary.total} ({summary.total ? Math.round((summary.pass / summary.total) * 100) : 0}%)
          </p>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-2">Gold labels by judge</h2>
        <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr><Th>Judge</Th><Th>Total</Th><Th>Pass</Th><Th>Fail</Th><Th>Hand</Th><Th>Auto</Th></tr>
          </thead>
          <tbody>
            {stats.map((s) => (
              <tr key={s.judge_name} className="border-t border-zinc-200 dark:border-zinc-800">
                <Td>{s.judge_name}</Td><Td>{s.total}</Td><Td>{s.pass}</Td>
                <Td>{s.fail}</Td><Td>{s.hand}</Td><Td>{s.auto}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Card({ title, value, href }: { title: string; value: number; href: string }) {
  return (
    <Link href={href} className="block p-4 border border-zinc-200 dark:border-zinc-800 rounded hover:bg-zinc-100 dark:hover:bg-zinc-900">
      <div className="text-sm text-zinc-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </Link>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-3 py-2">{children}</td>;
}
```

- [ ] **Step 2: Verify**

`npm run dev`. Visit `/`. Expect: three count cards (Cases→/cases, Fixed outputs→/cases, Gold labels→/judges), latest run card linking to most recent run, gold-labels-by-judge table preserved.

- [ ] **Step 3: Commit**

```bash
git add ui/app/page.tsx
git commit -m "ui: home page with repointed cards and latest-run summary"
```

---

## Task 23: Final smoke pass

- [ ] **Step 1: Type-check the full UI**

```bash
cd ui && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 2: Build**

```bash
cd ui && npm run build
```

Expected: build succeeds. All routes statically analysed.

- [ ] **Step 3: Smoke walk**

`npm run dev`, visit each route in turn:
- `/` — three cards, latest run card, gold-labels-by-judge.
- `/cases` — table with filters.
- `/cases/<id>` — three sections, gold-label save still works.
- `/runs` — list (unchanged).
- `/runs/<id>` — header summary line, judges-used in right rail.
- `/runs/<id>/trials/<id>` — two-column, expandable tool calls, judge-prompt disclosure, sidebar.
- `/runs/compare?a=&b=` — unchanged.
- `/agent` — config, inspector, graph, recent runs.
- `/judges` — cards link to `/judges/<name>`, table links to `/judges/runs/<id>`.
- `/judges/<name>` — current config, version history, gold stats.
- `/judges/<name>/<id>` — editor, activate, clone.
- `/judges/runs/<id>` — PR-run detail (relocated).
- `/golden`, `/prompts` — 404.

- [ ] **Step 4: Final commit**

```bash
git status
```

Expected: clean.

---

## Self-review notes (run after writing the plan)

**Spec coverage:**
- Sitemap: every route covered (Tasks 3, 6, 8-9, 13, 14, 17, 18, 21, 22).
- Top nav: Task 1.
- `/cases` columns + filters: Tasks 2-3.
- `/cases/[id]` three sections: Tasks 4-7.
- `/runs/[id]` summary header: Task 8.
- `/runs/[id]` judges-used in rail: Task 9.
- Trial detail two-column with input prominent, tool-call expansion, view-judge-prompt, sidebar: Tasks 10-13.
- `/agent` page: Tasks 20-21.
- `/judges` hub keeps layout, links updated: Task 14.
- `/judges/[name]`: Tasks 15-17.
- `/judges/[name]/[promptId]`: Task 18.
- Home with three cards + latest run: Task 22.
- `/golden` deleted: Task 7.
- `/prompts` deleted: Task 19.
- Open question (a) resolved: live values from `runs` row, static tools/graph (Task 21).
- Open question (b) resolved: parser reads `tool_calls.result` text (Task 10).

**Type consistency check:** `RunSummary`, `CaseIndexRow`, `CaseTrialHistoryRow`, `JudgePromptHistoryRow` referenced consistently. Server actions `updateCriterion`, `saveGoldLabel`, `updateFixedOutput` redefined under `app/cases/[id]/actions.ts` (with `case_id` form field added) — only callers are inside `app/cases/[id]/page.tsx`, which sends `case_id`. The `/judges/[name]` actions duplicate `/prompts/actions.ts` rather than reusing — intentional, since revalidate paths differ.
