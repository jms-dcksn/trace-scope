import Link from "next/link";
import { listCases, listCriteriaForCase } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default function CasesIndex() {
  const cases = listCases();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Cases & Criteria</h1>
      <p className="text-sm text-zinc-500">
        Edit criterion text. Note: editing invalidates downstream verdicts that reference the
        criterion_id — bump <code>PROMPT_VERSION</code> in the corresponding judge if semantics change.
      </p>
      <div className="space-y-3">
        {cases.map((c) => {
          const crits = listCriteriaForCase(c.case_id);
          return (
            <Link
              key={c.case_id}
              href={`/cases/${c.case_id}`}
              className="block border border-zinc-200 dark:border-zinc-800 rounded p-3 hover:bg-zinc-100 dark:hover:bg-zinc-900"
            >
              <div className="font-medium text-sm">#{c.case_id} {c.input}</div>
              <div className="text-xs text-zinc-500 mt-1">
                {crits.length} criteria · tags {c.tags}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
