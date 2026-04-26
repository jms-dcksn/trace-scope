import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getTrace,
  getTrial,
  getToolCallsForTrial,
  getVerdictsForTrial,
} from "@/lib/queries";
import { TrialReview, VerdictReview } from "./review-forms";

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
  const verdicts = getVerdictsForTrial(tId);
  const toolCalls = getToolCallsForTrial(tId);
  const trace = trial.trace_id ? getTrace(trial.trace_id) : null;
  const traceBlocks = trace ? splitTrace(trace.content) : [];

  const byJudge = verdicts.reduce<Record<string, typeof verdicts>>((acc, v) => {
    (acc[v.judge_name] ??= []).push(v);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/runs/${runId}`} className="text-sm text-blue-600 hover:underline">← Run #{runId}</Link>
        <h1 className="text-2xl font-semibold mt-1">
          Trial {trial.trial_id} · case {trial.case_id} · attempt {trial.trial_idx}
        </h1>
        <p className="text-sm text-zinc-500 mt-1 max-w-3xl">{trial.case_input}</p>
        <p className="text-xs text-zinc-500 mt-1">
          {trial.latency_ms ?? "—"}ms · in {trial.tokens_in ?? "—"} / out {trial.tokens_out ?? "—"} tok ·
          {trial.cost_usd != null ? ` $${trial.cost_usd.toFixed(4)}` : " —"}
        </p>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Reviewer notes (trial)</h2>
        <TrialReview trialId={tId} runId={runId} initialNotes={trial.reviewer_notes} />
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Agent output</h2>
        <pre className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded whitespace-pre-wrap font-sans">
          {trial.output}
        </pre>
      </section>

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
          </div>
        </section>
      ))}

      {toolCalls.length > 0 && (
        <section className="space-y-2">
          <h2 className="font-semibold">Tool calls ({toolCalls.length})</h2>
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr><Th>#</Th><Th>Tool</Th><Th>Args</Th><Th>Latency</Th></tr>
            </thead>
            <tbody>
              {toolCalls.map((tc) => (
                <tr key={tc.tool_call_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td>{tc.idx + 1}</Td>
                  <Td>{tc.tool_name}</Td>
                  <Td className="font-mono text-xs max-w-xl truncate" title={tc.args}>{tc.args}</Td>
                  <Td>{tc.latency_ms != null ? `${tc.latency_ms}ms` : "—"}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

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

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "", title }: { children: React.ReactNode; className?: string; title?: string }) {
  return <td className={`px-3 py-2 ${className}`} title={title}>{children}</td>;
}
