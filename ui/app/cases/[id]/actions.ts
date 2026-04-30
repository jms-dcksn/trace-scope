"use server";

import { revalidatePath } from "next/cache";
import { db, nowIso } from "@/lib/db";

export async function updateCriterion(formData: FormData) {
  const id = Number(formData.get("criterion_id"));
  const text = String(formData.get("text") ?? "").trim();
  if (!id || !text) throw new Error("missing criterion fields");
  db().prepare(`UPDATE criteria SET text = ? WHERE criterion_id = ?`).run(text, id);
  const caseId = formData.get("case_id");
  if (caseId) revalidatePath(`/cases/${caseId}`);
  revalidatePath(`/cases`);
}

export async function updateFixedOutput(formData: FormData) {
  const id = Number(formData.get("fixed_output_id"));
  const caseId = Number(formData.get("case_id"));
  const agentOutput = String(formData.get("agent_output") ?? "");
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id) throw new Error("missing fixed_output_id");
  db()
    .prepare(`UPDATE fixed_outputs SET agent_output = ?, notes = ? WHERE fixed_output_id = ?`)
    .run(agentOutput, notes, id);
  if (caseId) revalidatePath(`/cases/${caseId}`);
}

export async function saveGoldLabel(formData: FormData) {
  const fixedOutputId = Number(formData.get("fixed_output_id"));
  const criterionId = Number(formData.get("criterion_id"));
  const judgeName = String(formData.get("judge_name"));
  const labelStr = String(formData.get("label"));
  const labeler = String(formData.get("labeler") || "james").trim() || "james";
  const notes = String(formData.get("notes") || "") || null;
  const caseId = Number(formData.get("case_id"));
  if (!fixedOutputId || !criterionId || !judgeName) throw new Error("missing required fields");

  if (labelStr === "unset") {
    db()
      .prepare(`DELETE FROM gold_labels WHERE fixed_output_id = ? AND criterion_id = ? AND judge_name = ?`)
      .run(fixedOutputId, criterionId, judgeName);
  } else {
    const label = labelStr === "pass" ? 1 : 0;
    db()
      .prepare(
        `INSERT INTO gold_labels
           (criterion_id, fixed_output_id, judge_name, label, labeler, notes, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(criterion_id, fixed_output_id, judge_name)
         DO UPDATE SET label = excluded.label,
                       labeler = excluded.labeler,
                       notes = excluded.notes`,
      )
      .run(criterionId, fixedOutputId, judgeName, label, labeler, notes, nowIso());
  }

  if (caseId) revalidatePath(`/cases/${caseId}`);
}
