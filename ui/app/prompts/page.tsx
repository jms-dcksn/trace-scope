import Link from "next/link";
import { activePromptByJudge, listJudgeNames, listPromptsForJudge } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default function PromptsIndex() {
  const judges = listJudgeNames();
  const active = activePromptByJudge();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Judge Prompts</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Versioned templates. The active version is what runs. Clone to a new version before editing
          if you want to keep the previous one runnable.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {judges.map((j) => {
          const a = active[j];
          const versions = listPromptsForJudge(j);
          return (
            <Link
              key={j}
              href={`/prompts/${j}`}
              className="block border border-zinc-200 dark:border-zinc-800 rounded p-4 hover:bg-zinc-100 dark:hover:bg-zinc-900"
            >
              <div className="font-medium">{j}</div>
              <div className="text-sm text-zinc-500 mt-1">
                Active: <span className="font-mono">{a?.version ?? "—"}</span> · {versions.length} version{versions.length === 1 ? "" : "s"}
              </div>
              {a && (
                <p className="text-xs text-zinc-500 mt-2 line-clamp-3">
                  {a.template.slice(0, 200)}…
                </p>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
