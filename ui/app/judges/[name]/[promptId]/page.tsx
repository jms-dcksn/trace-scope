import Link from "next/link";
import { notFound } from "next/navigation";
import { getPrompt, PLACEHOLDERS, promptUsedByRunCount } from "@/lib/queries";
import { cloneAsNewVersion, savePrompt, setActive } from "../actions";

export const dynamic = "force-dynamic";

export default async function PromptVersionDetail({
  params,
}: {
  params: Promise<{ name: string; promptId: string }>;
}) {
  const { name, promptId } = await params;
  const id = Number(promptId);
  const p = getPrompt(id);
  if (!p || p.judge_name !== name) notFound();
  const placeholders = PLACEHOLDERS[name] ?? [];
  const usedBy = promptUsedByRunCount(name, p.version);

  return (
    <div className="space-y-6">
      <div className="text-sm text-blue-600">
        <Link href="/judges" className="hover:underline">Judges</Link>
        <span className="mx-1 text-zinc-400">→</span>
        <Link href={`/judges/${name}`} className="hover:underline">{name}</Link>
        <span className="mx-1 text-zinc-400">→</span>
        <span className="font-mono">v{p.version.replace(/^v/, "")}</span>
      </div>
      <h1 className="text-2xl font-semibold">
        <span className="font-mono">{p.version}</span>
        {p.is_active ? <span className="ml-2 text-sm text-green-600">● active</span> : null}
      </h1>
      <p className="text-sm text-zinc-500">
        Used by {usedBy} run{usedBy === 1 ? "" : "s"} · updated {p.updated_at}
      </p>
      {usedBy > 0 && (
        <p className="text-xs text-amber-600">
          ⚠ This version has been used by stored runs. Editing will retroactively change what those runs claim
          to have used. Consider &quot;Clone to new version&quot; instead.
        </p>
      )}

      {placeholders.length > 0 && (
        <section className="text-sm">
          <div className="text-zinc-500 mb-1">Placeholders available:</div>
          <div className="flex flex-wrap gap-2">
            {placeholders.map((ph) => (
              <code key={ph} className="px-2 py-1 bg-zinc-100 dark:bg-zinc-900 rounded text-xs">{`{${ph}}`}</code>
            ))}
          </div>
        </section>
      )}

      <section>
        <form action={savePrompt} className="space-y-2">
          <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
          <label className="block text-sm font-semibold">Template</label>
          <textarea name="template" defaultValue={p.template} rows={24}
            className="w-full p-3 font-mono text-xs border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <label className="block text-sm font-semibold mt-2">Notes</label>
          <textarea name="notes" defaultValue={p.notes ?? ""} rows={2}
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <button type="submit" className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            Save edits
          </button>
        </form>
      </section>

      <section className="grid grid-cols-2 gap-4">
        {!p.is_active && (
          <form action={setActive} className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2">
            <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
            <h3 className="font-semibold text-sm">Activate</h3>
            <p className="text-xs text-zinc-500">Mark this version active.</p>
            <button className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700">Set active</button>
          </form>
        )}
        <form action={cloneAsNewVersion} className="border border-zinc-200 dark:border-zinc-800 rounded p-3 space-y-2">
          <input type="hidden" name="judge_prompt_id" value={p.judge_prompt_id} />
          <h3 className="font-semibold text-sm">Clone to new version</h3>
          <input name="new_version" placeholder="e.g. v2" required
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <input name="notes" placeholder="what changed"
            className="w-full p-2 text-sm border border-zinc-300 dark:border-zinc-700 rounded bg-white dark:bg-zinc-950" />
          <button className="px-3 py-1.5 text-sm bg-zinc-700 text-white rounded hover:bg-zinc-800">Create new version</button>
        </form>
      </section>
    </div>
  );
}
