import { resolveJudgePrompt } from "@/lib/queries";

export function JudgePromptDisclosure({
  judgeName,
  version,
}: {
  judgeName: string;
  version: string | null;
}) {
  if (!version) return null;
  const prompt = resolveJudgePrompt(judgeName, version);
  if (!prompt) {
    return (
      <details className="mt-2 text-xs">
        <summary className="cursor-pointer text-blue-600 hover:underline">View judge prompt</summary>
        <p className="mt-1 text-zinc-500">Prompt {judgeName} v{version} not found in judge_prompts.</p>
      </details>
    );
  }
  return (
    <details className="mt-2 text-xs">
      <summary className="cursor-pointer text-blue-600 hover:underline">
        View judge prompt ({judgeName} <span className="font-mono">{version}</span>)
      </summary>
      <pre className="mt-2 p-3 rounded bg-zinc-100 dark:bg-zinc-900 whitespace-pre-wrap font-mono">{prompt.template}</pre>
      <p className="mt-1 text-zinc-500">
        Placeholders are filled at run-time by the judge with values like the agent input/output and evidence trace.
      </p>
    </details>
  );
}
