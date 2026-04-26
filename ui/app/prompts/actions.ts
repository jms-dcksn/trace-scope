"use server";

import { revalidatePath } from "next/cache";
import { db, nowIso } from "@/lib/db";

export async function savePrompt(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  const template = String(formData.get("template") ?? "");
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id || !template.trim()) throw new Error("missing required fields");

  db()
    .prepare(`UPDATE judge_prompts SET template = ?, notes = ?, updated_at = ? WHERE judge_prompt_id = ?`)
    .run(template, notes, nowIso(), id);

  const row = db()
    .prepare(`SELECT judge_name FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string } | undefined;
  if (row) revalidatePath(`/prompts/${row.judge_name}`);
  revalidatePath(`/prompts/${row?.judge_name ?? ""}/${id}`);
  revalidatePath(`/prompts`);
}

export async function setActive(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  if (!id) throw new Error("missing id");
  const row = db()
    .prepare(`SELECT judge_name FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string } | undefined;
  if (!row) throw new Error("not found");

  const tx = db().transaction(() => {
    db()
      .prepare(`UPDATE judge_prompts SET is_active = 0 WHERE judge_name = ?`)
      .run(row.judge_name);
    db()
      .prepare(`UPDATE judge_prompts SET is_active = 1, updated_at = ? WHERE judge_prompt_id = ?`)
      .run(nowIso(), id);
  });
  tx();

  revalidatePath(`/prompts/${row.judge_name}`);
  revalidatePath(`/prompts`);
}

export async function cloneAsNewVersion(formData: FormData) {
  const id = Number(formData.get("judge_prompt_id"));
  const newVersion = String(formData.get("new_version") ?? "").trim();
  const notes = String(formData.get("notes") ?? "") || null;
  if (!id || !newVersion) throw new Error("missing fields");

  const src = db()
    .prepare(`SELECT judge_name, template FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as { judge_name: string; template: string } | undefined;
  if (!src) throw new Error("source prompt not found");

  const ts = nowIso();
  db()
    .prepare(
      `INSERT INTO judge_prompts
         (judge_name, version, template, notes, is_active, created_at, updated_at)
       VALUES (?, ?, ?, ?, 0, ?, ?)`,
    )
    .run(src.judge_name, newVersion, src.template, notes, ts, ts);

  revalidatePath(`/prompts/${src.judge_name}`);
  revalidatePath(`/prompts`);
}
