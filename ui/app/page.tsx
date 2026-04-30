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
