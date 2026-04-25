import Link from "next/link";
import { notFound } from "next/navigation";
import { getCase, listCriteriaForCase } from "@/lib/queries";
import { updateCriterion } from "@/app/golden/actions";

export const dynamic = "force-dynamic";

export default async function CaseDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = Number(id);
  const c = getCase(caseId);
  if (!c) notFound();
  const crits = listCriteriaForCase(caseId);

  return (
    <div className="space-y-6">
      <div>
        <Link href="/cases" className="text-sm text-blue-600 hover:underline">← Cases</Link>
        <h1 className="text-2xl font-semibold mt-1">Case #{c.case_id}</h1>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Input</h2>
        <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded">{c.input}</p>
        {c.expected && (
          <>
            <h2 className="font-semibold mt-3">Expected</h2>
            <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded whitespace-pre-wrap">
              {c.expected}
            </p>
          </>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Criteria</h2>
        {crits.map((cr) => (
          <form
            key={cr.criterion_id}
            action={updateCriterion}
            className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2"
          >
            <input type="hidden" name="criterion_id" value={cr.criterion_id} />
            <input type="hidden" name="case_id" value={caseId} />
            <div className="text-xs text-zinc-500">
              {cr.judge_name} #{cr.idx} · id {cr.criterion_id}
            </div>
            <textarea
              name="text"
              defaultValue={cr.text}
              rows={2}
              className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
            />
            <button
              type="submit"
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Save criterion
            </button>
          </form>
        ))}
      </section>
    </div>
  );
}
