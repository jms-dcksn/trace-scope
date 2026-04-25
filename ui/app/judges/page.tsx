import Link from "next/link";
import { listJudgePrRuns, latestJudgePrRun } from "@/lib/queries";

export const dynamic = "force-dynamic";

const JUDGES = ["correctness", "faithfulness", "tool_use"] as const;

export default function JudgesIndex() {
  const runs = listJudgePrRuns();
  const latest = Object.fromEntries(
    JUDGES.map((j) => [j, latestJudgePrRun(j)]),
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Judge Health</h1>
        <p className="text-sm text-zinc-500 mt-1">
          P/R/F1 from <code>evals judge-pr</code>. Re-run the CLI to refresh.
        </p>
      </div>

      <section className="grid grid-cols-3 gap-4">
        {JUDGES.map((j) => {
          const r = latest[j];
          return (
            <div key={j} className="border border-zinc-200 dark:border-zinc-800 rounded p-4">
              <div className="font-medium">{j}</div>
              {r ? (
                <>
                  <div className="text-3xl font-semibold mt-2">
                    {(r.f1_pct * 100).toFixed(0)}<span className="text-base text-zinc-500">% F1</span>
                  </div>
                  <div className="text-xs text-zinc-500 mt-1">
                    P {(r.precision_pct * 100).toFixed(0)}% · R {(r.recall_pct * 100).toFixed(0)}% · n={r.total}
                  </div>
                  <Link
                    href={`/judges/${r.judge_pr_run_id}`}
                    className="text-xs text-blue-600 hover:underline mt-2 inline-block"
                  >
                    View detail →
                  </Link>
                </>
              ) : (
                <p className="text-sm text-zinc-500 mt-2">No runs yet.</p>
              )}
            </div>
          );
        })}
      </section>

      <section>
        <h2 className="font-semibold mb-2">Recent judge-pr runs</h2>
        <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr>
              <Th>ID</Th>
              <Th>Judge</Th>
              <Th>Model</Th>
              <Th>Prompt v</Th>
              <Th>Started</Th>
              <Th>n</Th>
              <Th>P</Th>
              <Th>R</Th>
              <Th>F1</Th>
              <Th>Auto</Th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.judge_pr_run_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <Td>
                  <Link href={`/judges/${r.judge_pr_run_id}`} className="text-blue-600 hover:underline">
                    {r.judge_pr_run_id}
                  </Link>
                </Td>
                <Td>{r.judge_name}</Td>
                <Td>{r.judge_model}</Td>
                <Td>{r.prompt_version}</Td>
                <Td className="text-xs">{r.started_at}</Td>
                <Td>{r.total}</Td>
                <Td>{(r.precision_pct * 100).toFixed(0)}%</Td>
                <Td>{(r.recall_pct * 100).toFixed(0)}%</Td>
                <Td className="font-medium">{(r.f1_pct * 100).toFixed(0)}%</Td>
                <Td>{r.auto_labeled}/{r.total}</Td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr><Td>—</Td><td colSpan={9} className="px-3 py-2 text-zinc-500">
                No judge-pr runs yet. Run <code>uv run python -m evals judge-pr --judge correctness</code>.
              </td></tr>
            )}
          </tbody>
        </table>
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
