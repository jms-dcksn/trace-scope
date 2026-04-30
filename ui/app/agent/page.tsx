import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import { AGENT_DEFAULT_MODEL, AGENT_SYSTEM_PROMPT, AGENT_TOOLS } from "@/lib/agent-info";
import { mostRecentRun, recentRunsByModel } from "@/lib/queries";

export const dynamic = "force-dynamic";

// Mirror of costs.py MODEL_COSTS (per 1k tokens, USD). Update if costs.py changes.
const MODEL_COSTS: Record<string, [number, number]> = {
  "gpt-5.4": [0.0025, 0.015],
  "gpt-5.4-mini": [0.00075, 0.0045],
  "gpt-5.4-nano": [0.0002, 0.00125],
};

export default function AgentPage() {
  const latest = mostRecentRun();
  const liveModel = latest?.agent_model ?? AGENT_DEFAULT_MODEL;
  const liveSystemPrompt = latest?.agent_system_prompt ?? AGENT_SYSTEM_PROMPT;
  const recentRuns = latest ? recentRunsByModel(latest.agent_model, 10) : [];
  const graphPath = path.resolve(process.cwd(), "lib", "agent-graph.mmd");
  const graph = fs.existsSync(graphPath) ? fs.readFileSync(graphPath, "utf-8") : "";
  const cost = MODEL_COSTS[liveModel.replace(/^openai:/, "")];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Agent harness</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Tavily-search LangChain agent. Live values come from the most recent run row;
          static metadata (tools, graph) is mirrored from <code>agent.py</code>.
        </p>
      </div>

      <section className="space-y-2">
        <h2 className="font-semibold">Configuration</h2>
        <table className="text-sm border border-zinc-200 dark:border-zinc-800">
          <tbody>
            <tr className="border-b border-zinc-200 dark:border-zinc-800"><Td className="font-medium">Model</Td><Td>{liveModel}</Td></tr>
            <tr className="border-b border-zinc-200 dark:border-zinc-800"><Td className="font-medium">Tools</Td><Td>{AGENT_TOOLS.map((t) => t.name).join(", ")}</Td></tr>
            <tr><Td className="font-medium">Cost / 1k tok (in/out)</Td><Td>{cost ? `$${cost[0]} / $${cost[1]}` : "—"}</Td></tr>
          </tbody>
        </table>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Inspector</h2>
        <details className="border border-zinc-200 dark:border-zinc-800 rounded">
          <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">System prompt</summary>
          <pre className="text-xs p-3 whitespace-pre-wrap font-mono">{liveSystemPrompt}</pre>
        </details>
        {AGENT_TOOLS.map((t) => (
          <details key={t.name} className="border border-zinc-200 dark:border-zinc-800 rounded">
            <summary className="cursor-pointer px-3 py-2 text-sm bg-zinc-100 dark:bg-zinc-900">Tool: {t.name}</summary>
            <div className="p-3 space-y-2 text-sm">
              <p>{t.description}</p>
              <div>
                <div className="text-xs text-zinc-500">Parameters</div>
                <ul className="list-disc list-inside text-xs">
                  {t.parameters.map((p) => (
                    <li key={p.name}><code>{p.name}</code> ({p.type}) — {p.description}</li>
                  ))}
                </ul>
              </div>
            </div>
          </details>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Graph</h2>
        <pre className="text-xs p-3 rounded bg-zinc-100 dark:bg-zinc-900 font-mono whitespace-pre-wrap">{graph || "(graph file missing)"}</pre>
        <p className="text-xs text-zinc-500">
          Source: <code>ui/lib/agent-graph.mmd</code>. Paste into a mermaid renderer to view.
        </p>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Recent runs using this agent ({liveModel})</h2>
        {recentRuns.length === 0 ? (
          <p className="text-sm text-zinc-500">No runs.</p>
        ) : (
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr><Th>Run</Th><Th>Started</Th><Th>Tag</Th><Th>Hash</Th></tr>
            </thead>
            <tbody>
              {recentRuns.map((r) => (
                <tr key={r.run_id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <Td><Link href={`/runs/${r.run_id}`} className="text-blue-600 hover:underline">#{r.run_id}</Link></Td>
                  <Td className="text-xs">{r.started_at}</Td>
                  <Td className="text-xs">{r.tag ?? "—"}</Td>
                  <Td className="font-mono text-xs">{r.config_hash.slice(0, 8)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-left px-3 py-2 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
