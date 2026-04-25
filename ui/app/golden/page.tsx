import Link from "next/link";
import { listFixedOutputs, getGoldLabelsForFixedOutput } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default function GoldenIndex() {
  const outputs = listFixedOutputs();
  const rows = outputs.map((o) => {
    const labels = getGoldLabelsForFixedOutput(o.fixed_output_id);
    const byJudge = labels.reduce<Record<string, { pass: number; fail: number; auto: number }>>(
      (acc, l) => {
        const j = (acc[l.judge_name] ??= { pass: 0, fail: 0, auto: 0 });
        if (l.label === 1) j.pass++;
        else j.fail++;
        if (l.labeler === "auto-from-case-level") j.auto++;
        return acc;
      },
      {},
    );
    return { ...o, byJudge };
  });

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">Golden Dataset</h1>
        <p className="text-sm text-zinc-500">
          Edit reference outputs and gold labels. Writes go straight to evals.db.
        </p>
      </div>
      <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            <Th>ID</Th>
            <Th>Case</Th>
            <Th>Output preview</Th>
            <Th>Correctness (P/F · auto)</Th>
            <Th>Faithfulness</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const c = r.byJudge.correctness;
            const f = r.byJudge.faithfulness;
            return (
              <tr key={r.fixed_output_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <Td>
                  <Link href={`/golden/${r.fixed_output_id}`} className="text-blue-600 hover:underline">
                    {r.fixed_output_id}
                  </Link>
                </Td>
                <Td className="max-w-xs truncate" title={r.case_input}>{r.case_input}</Td>
                <Td className="max-w-md truncate" title={r.agent_output}>
                  {r.agent_output.slice(0, 80)}…
                </Td>
                <Td>{c ? `${c.pass}/${c.fail} · ${c.auto} auto` : "—"}</Td>
                <Td>{f ? (f.pass ? "pass" : "fail") : "—"}</Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "", title }: { children: React.ReactNode; className?: string; title?: string }) {
  return <td className={`px-3 py-2 ${className}`} title={title}>{children}</td>;
}
