import Link from "next/link";
import { notFound } from "next/navigation";
import { listPromptsForJudge, PLACEHOLDERS, promptUsedByRunCount } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function JudgePromptList({ params }: { params: Promise<{ judge: string }> }) {
  const { judge } = await params;
  const prompts = listPromptsForJudge(judge);
  if (prompts.length === 0) notFound();
  const placeholders = PLACEHOLDERS[judge] ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Link href="/prompts" className="text-sm text-blue-600 hover:underline">← Prompts</Link>
        <h1 className="text-2xl font-semibold mt-1">{judge}</h1>
      </div>

      {placeholders.length > 0 && (
        <section className="text-sm">
          <div className="text-zinc-500 mb-1">Available placeholders (use these in the template):</div>
          <div className="flex flex-wrap gap-2">
            {placeholders.map((p) => (
              <code key={p} className="px-2 py-1 bg-zinc-100 dark:bg-zinc-900 rounded text-xs">
                {`{${p}}`}
              </code>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-2">
        <h2 className="font-semibold">Versions</h2>
        <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
          <thead className="bg-zinc-100 dark:bg-zinc-900">
            <tr>
              <Th>Version</Th>
              <Th>Active</Th>
              <Th>Used by runs</Th>
              <Th>Updated</Th>
              <Th>Notes</Th>
            </tr>
          </thead>
          <tbody>
            {prompts.map((p) => {
              const usedBy = promptUsedByRunCount(p.judge_name, p.version);
              return (
                <tr key={p.judge_prompt_id} className="border-t border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900">
                  <Td>
                    <Link href={`/prompts/${judge}/${p.judge_prompt_id}`} className="text-blue-600 hover:underline font-mono">
                      {p.version}
                    </Link>
                  </Td>
                  <Td>{p.is_active ? <span className="text-green-600">●</span> : "—"}</Td>
                  <Td>{usedBy}</Td>
                  <Td className="text-xs">{p.updated_at}</Td>
                  <Td className="text-xs text-zinc-500 max-w-md truncate" title={p.notes ?? ""}>{p.notes ?? "—"}</Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "", title }: { children: React.ReactNode; className?: string; title?: string }) {
  return <td className={`px-3 py-2 ${className}`} title={title}>{children}</td>;
}
