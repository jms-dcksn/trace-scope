"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

type Row = {
  run_id: number;
  started_at: string;
  agent_model: string;
  trial_count: number;
  mean_correctness: number | null;
  total_cost: number | null;
  tag: string | null;
  config_hash: string;
};

export default function RunsTable({ runs }: { runs: Row[] }) {
  const router = useRouter();
  const [selected, setSelected] = useState<number[]>([]);

  const toggle = (id: number) => {
    setSelected((s) => {
      if (s.includes(id)) return s.filter((x) => x !== id);
      if (s.length >= 2) return [s[1], id];
      return [...s, id];
    });
  };

  const canCompare = selected.length === 2;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-500">
          {selected.length === 0 && "Select two runs to compare."}
          {selected.length === 1 && "Select one more run to compare."}
          {selected.length === 2 && `Comparing #${selected[0]} vs #${selected[1]}.`}
        </p>
        <button
          disabled={!canCompare}
          onClick={() => router.push(`/runs/compare?a=${selected[0]}&b=${selected[1]}`)}
          className="px-3 py-1.5 text-sm rounded border border-zinc-300 dark:border-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
        >
          Compare
        </button>
      </div>

      <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            <Th></Th>
            <Th>ID</Th>
            <Th>Started</Th>
            <Th>Agent</Th>
            <Th>Trials</Th>
            <Th>Mean correctness</Th>
            <Th>Total cost</Th>
            <Th>Tag</Th>
            <Th>Hash</Th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.run_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
              <Td>
                <input
                  type="checkbox"
                  checked={selected.includes(r.run_id)}
                  onChange={() => toggle(r.run_id)}
                  aria-label={`Select run ${r.run_id}`}
                />
              </Td>
              <Td>
                <Link href={`/runs/${r.run_id}`} className="text-blue-600 hover:underline">{r.run_id}</Link>
              </Td>
              <Td className="text-xs">{r.started_at}</Td>
              <Td className="text-xs">{r.agent_model}</Td>
              <Td>{r.trial_count}</Td>
              <Td>{r.mean_correctness != null ? `${(r.mean_correctness * 100).toFixed(0)}%` : "—"}</Td>
              <Td>{r.total_cost != null ? `$${r.total_cost.toFixed(4)}` : "—"}</Td>
              <Td>{r.tag ?? "—"}</Td>
              <Td className="font-mono text-xs">{r.config_hash.slice(0, 8)}</Td>
            </tr>
          ))}
          {runs.length === 0 && (
            <tr><td colSpan={9} className="px-3 py-2 text-zinc-500">No runs yet. Run <code>uv run python -m evals run</code>.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
