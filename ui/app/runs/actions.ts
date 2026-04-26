"use server";

import { revalidatePath } from "next/cache";
import { db, nowIso } from "@/lib/db";

const FAILURE_MODES = new Set([
  "agent-error",
  "judge-too-strict",
  "judge-too-lenient",
  "gold-wrong",
  "criterion-ambiguous",
  "other",
]);

export async function saveVerdictReview(formData: FormData) {
  const verdictId = Number(formData.get("verdict_id"));
  const runId = Number(formData.get("run_id"));
  const trialId = Number(formData.get("trial_id"));
  const notesRaw = String(formData.get("reviewer_notes") ?? "").trim();
  const modeRaw = String(formData.get("failure_mode") ?? "").trim();
  if (!verdictId) throw new Error("missing verdict_id");

  const failureMode = modeRaw && FAILURE_MODES.has(modeRaw) ? modeRaw : null;
  const notes = notesRaw || null;
  const reviewedAt = notes || failureMode ? nowIso() : null;

  db()
    .prepare(
      `UPDATE criterion_verdicts
       SET reviewer_notes = ?, failure_mode = ?, reviewed_at = ?
       WHERE verdict_id = ?`,
    )
    .run(notes, failureMode, reviewedAt, verdictId);

  if (runId) revalidatePath(`/runs/${runId}`);
  if (runId && trialId) revalidatePath(`/runs/${runId}/trials/${trialId}`);
}

export async function saveTrialReview(formData: FormData) {
  const trialId = Number(formData.get("trial_id"));
  const runId = Number(formData.get("run_id"));
  const notes = String(formData.get("reviewer_notes") ?? "").trim() || null;
  if (!trialId) throw new Error("missing trial_id");
  db().prepare(`UPDATE trials SET reviewer_notes = ? WHERE trial_id = ?`).run(notes, trialId);
  if (runId) revalidatePath(`/runs/${runId}`);
  if (runId && trialId) revalidatePath(`/runs/${runId}/trials/${trialId}`);
}
