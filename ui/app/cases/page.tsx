import Link from "next/link";
import { listCaseIndexRows } from "@/lib/queries";

export const dynamic = "force-dynamic";

type FilterKey = "all" | "needs_labels" | "has_failures";

export default async function CasesIndex({
  searchParams,
}: {
  searchParams: Promise<{ filter?: FilterKey; tag?: string }>;
}) {
  const sp = await searchParams;
  const filter = (sp.filter ?? "all") as FilterKey;
  const tagFilter = sp.tag ?? "";

  const rows = listCaseIndexRows();
  const allTags = Array.from(
    new Set(
      rows.flatMap((r) => {
        try { return JSON.parse(r.tags) as string[]; } catch { return []; }
      }),
    ),
  ).sort();

  const filtered = rows.filter((r) => {
    if (filter === "needs_labels" && !r.needs_labels) return false;
    if (filter === "has_failures") {
      if (r.last_trial_pass == null || r.last_trial_total == null) return false;
      if (r.last_trial_pass === r.last_trial_total) return false;
    }
    if (tagFilter) {
      try { if (!(JSON.parse(r.tags) as string[]).includes(tagFilter)) return false; }
      catch { return false; }
    }
    return true;
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Cases</h1>

      <form className="flex flex-wrap gap-3 items-center text-sm">
        <label>
          Filter:
          <select name="filter" defaultValue={filter} className="ml-2 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
            <option value="all">All</option>
            <option value="needs_labels">Needs labels</option>
            <option value="has_failures">Has failures (last trial)</option>
          </select>
        </label>
        <label>
          Tag:
          <select name="tag" defaultValue={tagFilter} className="ml-2 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
            <option value="">(any)</option>
            {allTags.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        <button type="submit" className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Apply</button>
      </form>

      <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
        <thead className="bg-zinc-100 dark:bg-zinc-900">
          <tr>
            <Th>Case input</Th>
            <Th># crit</Th>
            <Th># fixed</Th>
            <Th>Correctness gold</Th>
            <Th>Faithfulness gold</Th>
            <Th>Last trial</Th>
            <Th>Tags</Th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((r) => (
            <tr key={r.case_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
              <Td>
                <Link href={`/cases/${r.case_id}`} className="text-blue-600 hover:underline">
                  #{r.case_id} {r.input}
                </Link>
                {r.needs_labels === 1 && (
                  <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">needs labels</span>
                )}
              </Td>
              <Td>{r.criteria_count}</Td>
              <Td>{r.fixed_output_count}</Td>
              <Td>{r.correctness_total ? `${r.correctness_pass}/${r.correctness_total} (${r.correctness_auto} auto)` : "—"}</Td>
              <Td>{r.faithfulness_total ? `${r.faithfulness_pass}/${r.faithfulness_total} (${r.faithfulness_auto} auto)` : "—"}</Td>
              <Td className="text-xs">
                {r.last_trial_id != null ? (
                  <Link href={`/runs/${r.last_trial_run_id}/trials/${r.last_trial_id}`} className="text-blue-600 hover:underline">
                    run #{r.last_trial_run_id} · {r.last_trial_pass ?? 0}/{r.last_trial_total ?? 0}
                  </Link>
                ) : "—"}
              </Td>
              <Td className="text-xs text-zinc-500">{r.tags}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
