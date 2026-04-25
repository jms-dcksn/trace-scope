import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getFixedOutput,
  getGoldLabelsForFixedOutput,
  listCriteriaForCase,
  getFaithfulnessCriterion,
} from "@/lib/queries";
import { saveGoldLabel, updateFixedOutput } from "../actions";

export const dynamic = "force-dynamic";

export default async function GoldenDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const foId = Number(id);
  const fo = getFixedOutput(foId);
  if (!fo) notFound();

  const correctnessCriteria = listCriteriaForCase(fo.case_id).filter(
    (c) => c.judge_name === "correctness",
  );
  const faithfulness = getFaithfulnessCriterion();
  const labels = getGoldLabelsForFixedOutput(foId);
  const labelMap = new Map<string, (typeof labels)[number]>();
  for (const l of labels) labelMap.set(`${l.criterion_id}:${l.judge_name}`, l);

  return (
    <div className="space-y-8">
      <div>
        <Link href="/golden" className="text-sm text-blue-600 hover:underline">← Golden Dataset</Link>
        <h1 className="text-2xl font-semibold mt-1">Fixed Output #{fo.fixed_output_id}</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Case {fo.case_id} · {fo.source ?? "—"} · created {fo.created_at}
        </p>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Case input</h2>
        <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded">{fo.case_input}</p>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Agent output</h2>
        <form action={updateFixedOutput} className="space-y-2">
          <input type="hidden" name="fixed_output_id" value={fo.fixed_output_id} />
          <textarea
            name="agent_output"
            defaultValue={fo.agent_output}
            rows={12}
            className="w-full p-3 font-mono text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
          />
          <textarea
            name="notes"
            defaultValue={fo.notes ?? ""}
            placeholder="notes (optional)"
            rows={2}
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
          />
          <button
            type="submit"
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Save output
          </button>
        </form>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Correctness gold labels</h2>
        {correctnessCriteria.length === 0 && (
          <p className="text-sm text-zinc-500">No correctness criteria for this case.</p>
        )}
        {correctnessCriteria.map((c) => {
          const label = labelMap.get(`${c.criterion_id}:correctness`);
          return (
            <LabelForm
              key={c.criterion_id}
              fixedOutputId={fo.fixed_output_id}
              criterionId={c.criterion_id}
              judgeName="correctness"
              criterionText={`#${c.idx} ${c.text}`}
              currentLabel={label?.label}
              currentLabeler={label?.labeler}
              currentNotes={label?.notes ?? ""}
            />
          );
        })}
      </section>

      {faithfulness && (
        <section className="space-y-3">
          <h2 className="font-semibold">Faithfulness gold label</h2>
          <LabelForm
            fixedOutputId={fo.fixed_output_id}
            criterionId={faithfulness.criterion_id}
            judgeName="faithfulness"
            criterionText={faithfulness.text}
            currentLabel={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.label}
            currentLabeler={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.labeler}
            currentNotes={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.notes ?? ""}
          />
        </section>
      )}
    </div>
  );
}

function LabelForm({
  fixedOutputId,
  criterionId,
  judgeName,
  criterionText,
  currentLabel,
  currentLabeler,
  currentNotes,
}: {
  fixedOutputId: number;
  criterionId: number;
  judgeName: string;
  criterionText: string;
  currentLabel: number | undefined;
  currentLabeler: string | undefined;
  currentNotes: string;
}) {
  const current =
    currentLabel === 1 ? "pass" : currentLabel === 0 ? "fail" : "unset";
  const isAuto = currentLabeler === "auto-from-case-level";
  return (
    <form
      action={saveGoldLabel}
      className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2"
    >
      <input type="hidden" name="fixed_output_id" value={fixedOutputId} />
      <input type="hidden" name="criterion_id" value={criterionId} />
      <input type="hidden" name="judge_name" value={judgeName} />
      <p className="text-sm">{criterionText}</p>
      <div className="flex flex-wrap gap-3 items-center text-sm">
        <label className="flex items-center gap-1">
          Label:
          <select
            name="label"
            defaultValue={current}
            className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950"
          >
            <option value="pass">pass</option>
            <option value="fail">fail</option>
            <option value="unset">unset (delete)</option>
          </select>
        </label>
        <label className="flex items-center gap-1">
          Labeler:
          <input
            name="labeler"
            defaultValue={currentLabeler ?? "james"}
            className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950 w-40"
          />
        </label>
        {isAuto && (
          <span className="text-amber-600 text-xs">⚠ auto-broadcast — needs review</span>
        )}
      </div>
      <textarea
        name="notes"
        defaultValue={currentNotes}
        placeholder="rationale (optional)"
        rows={2}
        className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
      />
      <button
        type="submit"
        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Save label
      </button>
    </form>
  );
}
