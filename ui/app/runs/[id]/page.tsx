import Link from "next/link";
import { notFound } from "next/navigation";
import {
  caseRollupForRun,
  failureModeCountsForRun,
  getPromptIdByJudgeAndVersion,
  getRun,
  listTrialsForRun,
  reviewedCountsForRun,
} from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function RunDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const runId = Number(id);
  const run = getRun(runId);
  if (!run) notFound();
  const rollup = caseRollupForRun(runId);
  const trials = listTrialsForRun(runId);
  const reviewed = reviewedCountsForRun(runId);
  const failureModes = failureModeCountsForRun(runId);
  const trialsByCase = trials.reduce<Record<number, typeof trials>>((acc, t) => {
    (acc[t.case_id] ??= []).push(t);
    return acc;
  }, {});

  const judgeModels = JSON.parse(run.judge_models) as Record<string, string>;
  const judgeVersions = JSON.parse(run.judge_prompt_versions) as Record<string, string>;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/runs" className="text-sm text-blue-600 hover:underline">← Runs</Link>
        <h1 className="text-2xl font-semibold mt-1">Run #{run.run_id}</h1>
        <p className="text-sm text-zinc-500 mt-1">
          {run.agent_model} · started {run.started_at} · {run.trials_per_case} trials/case
        </p>
        <p className="text-xs text-zinc-500 mt-1">config_hash <code>{run.config_hash}</code></p>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Judges used</h2>
        <table className="text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr><Th>Judge</Th><Th>Model</Th><Th>Prompt version</Th></tr>
          </thead>
          <tbody>
            {Object.keys(judgeModels).map((j) => {
              const v = judgeVersions[j];
              const pid = v ? getPromptIdByJudgeAndVersion(j, v) : undefined;
              return (
                <tr key={j} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td>{j}</Td>
                  <Td>{judgeModels[j]}</Td>
                  <Td>
                    {pid ? (
                      <Link href={`/prompts/${j}/${pid}`} className="text-blue-600 hover:underline font-mono">
                        {v}
                      </Link>
                    ) : (
                      <span className="font-mono">{v ?? "—"}</span>
                    )}
                  </Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-6">
        <section>
          <h2 className="font-semibold mb-2">Per-case rollup</h2>
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr>
                <Th>Case</Th>
                <Th>Trials</Th>
                <Th>Correctness</Th>
                <Th>Faithfulness</Th>
                <Th>Tool use</Th>
                <Th>Avg latency</Th>
                <Th>Cost</Th>
                <Th>Trials</Th>
              </tr>
            </thead>
            <tbody>
              {rollup.map((r) => {
                const reviewedN = reviewed.get(r.case_id) ?? 0;
                const trialsForCase = trialsByCase[r.case_id] ?? [];
                const errored = trialsForCase.filter((t) => t.error).length;
                return (
                  <tr key={r.case_id} className="border-t border-zinc-200 dark:border-zinc-800">
                    <Td className="max-w-md truncate" title={r.case_input}>
                      #{r.case_id} {r.case_input}
                      {reviewedN > 0 && (
                        <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                          {reviewedN} reviewed
                        </span>
                      )}
                      {errored > 0 && (
                        <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-800">
                          {errored} error
                        </span>
                      )}
                    </Td>
                    <Td>{r.trials}</Td>
                    <Td>{r.correctness_total ? `${r.correctness_pass}/${r.correctness_total}` : "—"}</Td>
                    <Td>{r.faithfulness_total ? `${r.faithfulness_pass}/${r.faithfulness_total}` : "—"}</Td>
                    <Td>{r.tool_use_total ? `${r.tool_use_pass}/${r.tool_use_total}` : "—"}</Td>
                    <Td>{r.p50_latency_ms != null ? `${Math.round(r.p50_latency_ms)}ms` : "—"}</Td>
                    <Td>{r.total_cost != null ? `$${r.total_cost.toFixed(4)}` : "—"}</Td>
                    <Td className="text-xs space-x-2">
                      {trialsForCase.map((t) => (
                        <Link
                          key={t.trial_id}
                          href={`/runs/${runId}/trials/${t.trial_id}`}
                          className={`hover:underline ${t.error ? "text-red-600" : "text-blue-600"}`}
                          title={t.error ?? undefined}
                        >
                          #{t.trial_idx}{t.error ? "!" : ""}
                        </Link>
                      ))}
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        <aside className="space-y-2">
          <h2 className="font-semibold">Failure modes</h2>
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
        </aside>
      </div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "", title }: { children: React.ReactNode; className?: string; title?: string }) {
  return <td className={`px-3 py-2 ${className}`} title={title}>{children}</td>;
}
