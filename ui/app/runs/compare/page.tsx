import Link from "next/link";
import { notFound } from "next/navigation";
import { compareRuns, type CaseDelta, type CriterionDelta } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function CompareRuns({
  searchParams,
}: {
  searchParams: Promise<{ a?: string; b?: string }>;
}) {
  const { a, b } = await searchParams;
  const aId = Number(a);
  const bId = Number(b);
  if (!aId || !bId || aId === bId) notFound();

  const cmp = compareRuns(aId, bId);
  if (!cmp) notFound();

  // Group criteria by case+judge for drill-in.
  const critByCase = new Map<string, CriterionDelta[]>();
  for (const c of cmp.criteria) {
    const k = `${c.case_id ?? "null"}`;
    if (!critByCase.has(k)) critByCase.set(k, []);
    critByCase.get(k)!.push(c);
  }

  const judgeAModels = JSON.parse(cmp.a.judge_models) as Record<string, string>;
  const judgeBModels = JSON.parse(cmp.b.judge_models) as Record<string, string>;
  const judgeAVer = JSON.parse(cmp.a.judge_prompt_versions) as Record<string, string>;
  const judgeBVer = JSON.parse(cmp.b.judge_prompt_versions) as Record<string, string>;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/runs" className="text-sm text-blue-600 hover:underline">← Runs</Link>
        <h1 className="text-2xl font-semibold mt-1">
          Compare run #{cmp.a.run_id} vs #{cmp.b.run_id}
        </h1>
      </div>

      {cmp.configHashDiffers && (
        <div className="border border-amber-400 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 text-sm rounded">
          <div className="font-semibold text-amber-800 dark:text-amber-200">
            ⚠ config_hash differs — apples-to-oranges comparison
          </div>
          <div className="text-amber-800 dark:text-amber-200 mt-1">
            Differing fields: <code>{cmp.fieldDiffs.filter((f) => f !== "config_hash").join(", ") || "(only config_hash)"}</code>
          </div>
        </div>
      )}

      <section className="grid grid-cols-2 gap-4 text-sm">
        <RunHeader run={cmp.a} label="A" diffs={cmp.fieldDiffs} other={cmp.b} judgeModels={judgeAModels} judgeVer={judgeAVer} />
        <RunHeader run={cmp.b} label="B" diffs={cmp.fieldDiffs} other={cmp.a} judgeModels={judgeBModels} judgeVer={judgeBVer} />
      </section>

      <section>
        <h2 className="font-semibold mb-2">Per-case rollup</h2>
        <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr>
              <Th>Case</Th>
              <Th>Correctness A/B/Δ</Th>
              <Th>Faithfulness A/B/Δ</Th>
              <Th>Tool use A/B/Δ</Th>
              <Th>Latency A/B/Δ</Th>
              <Th>Cost A/B/Δ</Th>
            </tr>
          </thead>
          <tbody>
            {cmp.cases.map((c) => (
              <CaseRow
                key={c.case_id}
                runA={cmp.a.run_id}
                runB={cmp.b.run_id}
                row={c}
                criteria={critByCase.get(`${c.case_id}`) ?? []}
              />
            ))}
            {cmp.cases.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-2 text-zinc-500">No overlapping cases.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      {critByCase.has("null") && (
        <section>
          <h2 className="font-semibold mb-2">Global criteria</h2>
          <CriteriaTable rows={critByCase.get("null")!} />
        </section>
      )}

      {cmp.failureModeDeltas.length > 0 && (
        <section>
          <h2 className="font-semibold mb-2">Failure-mode deltas</h2>
          <p className="text-xs text-zinc-500 mb-2">
            Criteria where reviewer-tagged failure modes differ between A and B — the &quot;did the fix work&quot; signal.
          </p>
          <table className="w-full text-xs border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr>
                <Th>Case</Th>
                <Th>Judge</Th>
                <Th>#</Th>
                <Th>Criterion</Th>
                <Th>A modes</Th>
                <Th>B modes</Th>
              </tr>
            </thead>
            <tbody>
              {cmp.failureModeDeltas.map((d) => (
                <tr key={`${d.case_id ?? "null"}|${d.judge_name}|${d.idx}`} className="border-t border-zinc-200 dark:border-zinc-800">
                  <td className="px-2 py-1">{d.case_id == null ? "(global)" : `#${d.case_id}`}</td>
                  <td className="px-2 py-1">{d.judge_name}</td>
                  <td className="px-2 py-1">{d.idx}</td>
                  <td className="px-2 py-1 max-w-md truncate" title={d.text}>{d.text}</td>
                  <td className="px-2 py-1 font-mono">{d.a_modes.join(", ") || "—"}</td>
                  <td className="px-2 py-1 font-mono">{d.b_modes.join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function RunHeader({
  run, label, diffs, other, judgeModels, judgeVer,
}: {
  run: any; label: string; diffs: string[]; other: any;
  judgeModels: Record<string, string>; judgeVer: Record<string, string>;
}) {
  const flag = (field: string, val: any) =>
    diffs.includes(field) ? <strong className="text-amber-700 dark:text-amber-300">{String(val)}</strong> : <>{String(val)}</>;
  return (
    <div className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-1">
      <div className="font-semibold">
        Run {label} —{" "}
        <Link href={`/runs/${run.run_id}`} className="text-blue-600 hover:underline">
          #{run.run_id}
        </Link>
      </div>
      <div className="text-xs text-zinc-500">{run.started_at}</div>
      <div>Agent: {flag("agent_model", run.agent_model)}</div>
      <div>Trials/case: {flag("trials_per_case", run.trials_per_case)}</div>
      <div>Tag: {flag("tag", run.tag ?? "—")}</div>
      <div className="font-mono text-xs">
        config_hash: {flag("config_hash", run.config_hash.slice(0, 12))}
      </div>
      <div className="text-xs">
        Judges: {Object.keys(judgeModels).map((j) => (
          <span key={j} className="mr-2">
            {j}=<code>{judgeModels[j]}</code>@<code>{judgeVer[j] ?? "?"}</code>
          </span>
        ))}
      </div>
    </div>
  );
}

function CaseRow({
  runA, runB, row, criteria,
}: {
  runA: number; runB: number; row: CaseDelta; criteria: CriterionDelta[];
}) {
  const c = row.judges.find((j) => j.judge_name === "correctness")!;
  const f = row.judges.find((j) => j.judge_name === "faithfulness")!;
  const t = row.judges.find((j) => j.judge_name === "tool_use")!;
  return (
    <>
      <tr className="border-t border-zinc-200 dark:border-zinc-800 align-top">
        <td className="px-3 py-2 max-w-md">
          <details>
            <summary className="cursor-pointer">
              <span className="text-zinc-500">#{row.case_id}</span> {row.case_input}
            </summary>
            <div className="mt-2 space-x-2 text-xs">
              {row.a && <Link href={`/runs/${runA}`} className="text-blue-600 hover:underline">A trials</Link>}
              {row.b && <Link href={`/runs/${runB}`} className="text-blue-600 hover:underline">B trials</Link>}
            </div>
            {criteria.length > 0 && (
              <div className="mt-2">
                <CriteriaTable rows={criteria} compact />
              </div>
            )}
          </details>
        </td>
        <JudgeCell j={c} />
        <JudgeCell j={f} />
        <JudgeCell j={t} />
        <td className="px-3 py-2 text-xs">
          {fmtMs(row.latency_a)} / {fmtMs(row.latency_b)} /{" "}
          <DeltaSpan v={row.latency_delta ?? 0} fmt={fmtMs} invert />
        </td>
        <td className="px-3 py-2 text-xs">
          {fmtCost(row.cost_a)} / {fmtCost(row.cost_b)} /{" "}
          <DeltaSpan v={row.cost_delta} fmt={fmtCost} invert />
        </td>
      </tr>
    </>
  );
}

function JudgeCell({ j }: { j: CaseDelta["judges"][number] }) {
  if (j.a_total === 0 && j.b_total === 0) {
    return <td className="px-3 py-2 text-zinc-400">—</td>;
  }
  const ap = j.a_total ? j.a_pass / j.a_total : 0;
  const bp = j.b_total ? j.b_pass / j.b_total : 0;
  return (
    <td className="px-3 py-2 text-xs">
      <span>{j.a_pass}/{j.a_total} ({pct(ap)})</span>
      {" / "}
      <span>{j.b_pass}/{j.b_total} ({pct(bp)})</span>
      {" / "}
      <DeltaPct delta={j.delta} significant={j.significant} />
    </td>
  );
}

function CriteriaTable({ rows, compact }: { rows: CriterionDelta[]; compact?: boolean }) {
  return (
    <table className={`text-xs border border-zinc-200 dark:border-zinc-800 ${compact ? "" : "w-full"}`}>
      <thead className="bg-zinc-100 dark:bg-zinc-900">
        <tr>
          <Th>Judge</Th>
          <Th>#</Th>
          <Th>Criterion</Th>
          <Th>A</Th>
          <Th>B</Th>
          <Th>Δ</Th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={`${r.case_id}|${r.judge_name}|${r.idx}`} className="border-t border-zinc-200 dark:border-zinc-800">
            <td className="px-2 py-1">{r.judge_name}</td>
            <td className="px-2 py-1">{r.idx}</td>
            <td className="px-2 py-1 max-w-md truncate" title={r.text}>{r.text}</td>
            <td className="px-2 py-1">{r.a_pass}/{r.a_total} ({pct(r.a_p)})</td>
            <td className="px-2 py-1">{r.b_pass}/{r.b_total} ({pct(r.b_p)})</td>
            <td className="px-2 py-1"><DeltaPct delta={r.delta} significant={r.significant} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DeltaPct({ delta, significant }: { delta: number; significant: boolean }) {
  const arrow = delta > 0.0001 ? "↑" : delta < -0.0001 ? "↓" : "·";
  const cls =
    delta > 0.0001 ? "text-green-700 dark:text-green-400"
    : delta < -0.0001 ? "text-red-700 dark:text-red-400"
    : "text-zinc-500";
  return (
    <span className={cls}>
      {arrow} {(delta * 100).toFixed(0)}%
      {significant && <span className="ml-1 px-1 rounded bg-amber-200 text-amber-900 text-[10px]">sig</span>}
    </span>
  );
}

function DeltaSpan({ v, fmt, invert }: { v: number; fmt: (n: number | null) => string; invert?: boolean }) {
  // invert=true means lower is better (latency, cost)
  const better = invert ? v < 0 : v > 0;
  const worse = invert ? v > 0 : v < 0;
  const cls = better ? "text-green-700 dark:text-green-400"
    : worse ? "text-red-700 dark:text-red-400"
    : "text-zinc-500";
  const sign = v > 0 ? "+" : "";
  return <span className={cls}>{sign}{fmt(v)}</span>;
}

function pct(p: number): string {
  return `${Math.round(p * 100)}%`;
}
function fmtMs(n: number | null): string {
  if (n == null) return "—";
  return `${Math.round(n)}ms`;
}
function fmtCost(n: number | null): string {
  if (n == null) return "—";
  return `$${n.toFixed(4)}`;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
