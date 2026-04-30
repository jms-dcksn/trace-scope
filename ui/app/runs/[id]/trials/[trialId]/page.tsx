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
