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
