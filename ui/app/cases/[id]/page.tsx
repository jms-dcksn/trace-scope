import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getCase,
  listCriteriaForCase,
  listFixedOutputs,
  getGoldLabelsForFixedOutput,
  getFaithfulnessCriterion,
  listTrialHistoryForCase,
} from "@/lib/queries";
import { updateCriterion, updateFixedOutput, saveGoldLabel } from "./actions";

export const dynamic = "force-dynamic";

export default async function CaseDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = Number(id);
  const c = getCase(caseId);
  if (!c) notFound();
  const crits = listCriteriaForCase(caseId);
  const fixedOutputs = listFixedOutputs().filter((f) => f.case_id === caseId);
  const faithfulness = getFaithfulnessCriterion();
  const trials = listTrialHistoryForCase(caseId);

  return (
    <div className="space-y-8">
      <div>
        <Link href="/cases" className="text-sm text-blue-600 hover:underline">← Cases</Link>
        <h1 className="text-2xl font-semibold mt-1">Case #{c.case_id}</h1>
      </div>

      {/* 1. Definition */}
      <section className="space-y-3">
        <h2 className="font-semibold">Definition</h2>
        <div>
          <div className="text-xs text-zinc-500 mb-1">Input</div>
          <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded">{c.input}</p>
        </div>
        {c.expected && (
          <div>
            <div className="text-xs text-zinc-500 mb-1">Expected</div>
            <p className="text-sm bg-zinc-100 dark:bg-zinc-900 p-3 rounded whitespace-pre-wrap">{c.expected}</p>
          </div>
        )}
        <p className="text-xs text-zinc-500">
          Editing a criterion invalidates downstream verdicts referencing it — bump <code>PROMPT_VERSION</code>
          in the corresponding judge if semantics change.
        </p>
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
            <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
              Save criterion
            </button>
          </form>
        ))}
      </section>

      {/* 2. Golden record */}
      <section className="space-y-3">
        <h2 className="font-semibold">Golden record ({fixedOutputs.length})</h2>
        {fixedOutputs.length === 0 && <p className="text-sm text-zinc-500">No fixed outputs.</p>}
        {fixedOutputs.map((fo) => {
          const labels = getGoldLabelsForFixedOutput(fo.fixed_output_id);
          const labelMap = new Map(labels.map((l) => [`${l.criterion_id}:${l.judge_name}`, l]));
          const correctnessCriteria = crits.filter((c) => c.judge_name === "correctness");
          return (
            <details key={fo.fixed_output_id} className="border border-zinc-200 dark:border-zinc-800 rounded">
              <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">
                Fixed output #{fo.fixed_output_id} · {fo.source ?? "—"} · {fo.created_at}
              </summary>
              <div className="p-3 space-y-4">
                <form action={updateFixedOutput} className="space-y-2">
                  <input type="hidden" name="fixed_output_id" value={fo.fixed_output_id} />
                  <input type="hidden" name="case_id" value={caseId} />
                  <label className="text-xs text-zinc-500">Agent output</label>
                  <textarea
                    name="agent_output"
                    defaultValue={fo.agent_output}
                    rows={10}
                    className="w-full p-3 font-mono text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
                  />
                  <textarea
                    name="notes"
                    defaultValue={fo.notes ?? ""}
                    placeholder="notes (optional)"
                    rows={2}
                    className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950"
                  />
                  <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                    Save output
                  </button>
                </form>

                <div className="space-y-2">
                  <h3 className="text-sm font-semibold">Correctness gold labels</h3>
                  {correctnessCriteria.map((cr) => {
                    const l = labelMap.get(`${cr.criterion_id}:correctness`);
                    return (
                      <LabelForm
                        key={cr.criterion_id}
                        fixedOutputId={fo.fixed_output_id}
                        caseId={caseId}
                        criterionId={cr.criterion_id}
                        judgeName="correctness"
                        criterionText={`#${cr.idx} ${cr.text}`}
                        currentLabel={l?.label}
                        currentLabeler={l?.labeler}
                        currentNotes={l?.notes ?? ""}
                      />
                    );
                  })}
                </div>

                {faithfulness && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold">Faithfulness gold label</h3>
                    <LabelForm
                      fixedOutputId={fo.fixed_output_id}
                      caseId={caseId}
                      criterionId={faithfulness.criterion_id}
                      judgeName="faithfulness"
                      criterionText={faithfulness.text}
                      currentLabel={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.label}
                      currentLabeler={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.labeler}
                      currentNotes={labelMap.get(`${faithfulness.criterion_id}:faithfulness`)?.notes ?? ""}
                    />
                  </div>
                )}
              </div>
            </details>
          );
        })}
      </section>

      {/* 3. Trial history */}
      <section className="space-y-2">
        <h2 className="font-semibold">Trial history ({trials.length})</h2>
        {trials.length === 0 && <p className="text-sm text-zinc-500">No trials yet.</p>}
        {trials.length > 0 && (
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr>
                <Th>Run</Th><Th>Started</Th><Th>Attempt</Th>
                <Th>Correctness</Th><Th>Faithfulness</Th><Th>Tool use</Th>
                <Th>Latency</Th><Th>Cost</Th><Th>Trial</Th>
              </tr>
            </thead>
            <tbody>
              {trials.map((t) => (
                <tr key={t.trial_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td>#{t.run_id}</Td>
                  <Td className="text-xs">{t.started_at}</Td>
                  <Td>{t.trial_idx}</Td>
                  <Td>{t.correctness_total ? `${t.correctness_pass}/${t.correctness_total}` : "—"}</Td>
                  <Td>{t.faithfulness_total ? `${t.faithfulness_pass}/${t.faithfulness_total}` : "—"}</Td>
                  <Td>{t.tool_use_total ? `${t.tool_use_pass}/${t.tool_use_total}` : "—"}</Td>
                  <Td>{t.latency_ms != null ? `${t.latency_ms}ms` : "—"}</Td>
                  <Td>{t.cost_usd != null ? `$${t.cost_usd.toFixed(4)}` : "—"}</Td>
                  <Td>
                    <Link href={`/runs/${t.run_id}/trials/${t.trial_id}`} className="text-blue-600 hover:underline">
                      open →
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function LabelForm({
  fixedOutputId, caseId, criterionId, judgeName, criterionText,
  currentLabel, currentLabeler, currentNotes,
}: {
  fixedOutputId: number;
  caseId: number;
  criterionId: number;
  judgeName: string;
  criterionText: string;
  currentLabel: number | undefined;
  currentLabeler: string | undefined;
  currentNotes: string;
}) {
  const current = currentLabel === 1 ? "pass" : currentLabel === 0 ? "fail" : "unset";
  const isAuto = currentLabeler === "auto-from-case-level";
  return (
    <form action={saveGoldLabel} className="border border-zinc-200 dark:border-zinc-800 rounded p-2 space-y-2">
      <input type="hidden" name="fixed_output_id" value={fixedOutputId} />
      <input type="hidden" name="case_id" value={caseId} />
      <input type="hidden" name="criterion_id" value={criterionId} />
      <input type="hidden" name="judge_name" value={judgeName} />
      <p className="text-xs">{criterionText}</p>
      <div className="flex flex-wrap gap-2 items-center text-xs">
        <select name="label" defaultValue={current} className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950">
          <option value="pass">pass</option>
          <option value="fail">fail</option>
          <option value="unset">unset (delete)</option>
        </select>
        <input name="labeler" defaultValue={currentLabeler ?? "james"} className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-white dark:bg-zinc-950 w-32" />
        {isAuto && <span className="text-amber-600">⚠ auto</span>}
        <button className="px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
      </div>
      <textarea name="notes" defaultValue={currentNotes} placeholder="rationale" rows={1} className="w-full p-1 text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
    </form>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
