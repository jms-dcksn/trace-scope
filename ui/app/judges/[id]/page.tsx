import Link from "next/link";
import { notFound } from "next/navigation";
import { db } from "@/lib/db";
import { getJudgePrRows, type JudgePrRun } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function JudgePrDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const runId = Number(id);
  const run = db()
    .prepare(`SELECT * FROM judge_pr_runs WHERE judge_pr_run_id = ?`)
    .get(runId) as JudgePrRun | undefined;
  if (!run) notFound();

  const rows = getJudgePrRows(runId);
  const byOutcome = rows.reduce<Record<string, typeof rows>>((acc, r) => {
    (acc[r.outcome] ??= []).push(r);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <Link href="/judges" className="text-sm text-blue-600 hover:underline">← Judge Health</Link>
        <h1 className="text-2xl font-semibold mt-1">
          {run.judge_name} · run {run.judge_pr_run_id}
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          {run.judge_model} · prompt {run.prompt_version} · {run.started_at} · {(run.elapsed_ms / 1000).toFixed(1)}s
        </p>
      </div>

      <section className="grid grid-cols-4 gap-3 text-sm">
        <Stat label="Precision" value={`${(run.precision_pct * 100).toFixed(1)}%`} />
        <Stat label="Recall" value={`${(run.recall_pct * 100).toFixed(1)}%`} />
        <Stat label="F1" value={`${(run.f1_pct * 100).toFixed(1)}%`} highlight />
        <Stat label="Accuracy" value={`${(run.accuracy_pct * 100).toFixed(1)}%`} />
      </section>

      <section>
        <h2 className="font-semibold mb-2">Confusion matrix</h2>
        <table className="text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr><Th>{""}</Th><Th>Pred pass</Th><Th>Pred fail</Th></tr>
          </thead>
          <tbody>
            <tr className="border-t border-zinc-200 dark:border-zinc-800">
              <Td className="font-medium">Gold pass</Td>
              <Td className="text-green-600">{run.tp} TP</Td>
              <Td className="text-red-600">{run.fn} FN</Td>
            </tr>
            <tr className="border-t border-zinc-200 dark:border-zinc-800">
              <Td className="font-medium">Gold fail</Td>
              <Td className="text-red-600">{run.fp} FP</Td>
              <Td className="text-green-600">{run.tn} TN</Td>
            </tr>
          </tbody>
        </table>
        <p className="text-xs text-zinc-500 mt-2">
          {run.auto_labeled} of {run.total} examples used auto-broadcast labels — disagreements among these are the priority worklist.
        </p>
      </section>

      <section className="space-y-4">
        {(["FP", "FN", "TP", "TN"] as const).map((o) => {
          const list = byOutcome[o] || [];
          if (!list.length) return null;
          const isError = o === "FP" || o === "FN";
          return (
            <div key={o}>
              <h3 className={`font-semibold mb-1 ${isError ? "text-red-600" : ""}`}>
                {o} ({list.length})
              </h3>
              <table className="w-full text-xs border border-zinc-200 dark:border-zinc-800">
                <thead className="bg-zinc-100 dark:bg-zinc-900">
                  <tr>
                    <Th>fixed_output</Th>
                    <Th>case</Th>
                    <Th>criterion</Th>
                    <Th>gold</Th>
                    <Th>predicted</Th>
                    <Th>labeler</Th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((r) => (
                    <tr key={r.judge_pr_row_id} className="border-t border-zinc-200 dark:border-zinc-800">
                      <Td>
                        <Link href={`/cases/${r.case_id}`} className="text-blue-600 hover:underline">
                          fo #{r.fixed_output_id}
                        </Link>
                      </Td>
                      <Td className="max-w-[12rem] truncate" title={r.case_input}>{r.case_input}</Td>
                      <Td className="max-w-[20rem] truncate" title={r.criterion_text}>{r.criterion_text}</Td>
                      <Td>{r.gold}</Td>
                      <Td>{r.predicted}</Td>
                      <Td className={r.labeler === "auto-from-case-level" ? "text-amber-600" : ""}>
                        {r.labeler}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })}
      </section>
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`border rounded p-3 ${highlight ? "border-blue-500 bg-blue-50 dark:bg-blue-950" : "border-zinc-200 dark:border-zinc-800"}`}>
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "", title }: { children: React.ReactNode; className?: string; title?: string }) {
  return <td className={`px-3 py-2 ${className}`} title={title}>{children}</td>;
}
