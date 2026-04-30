"use client";

import { useState } from "react";
import { parseTavilyResult } from "@/lib/parse-tavily";

export function ToolCallRow({
  idx,
  toolName,
  args,
  result,
  latencyMs,
}: {
  idx: number;
  toolName: string;
  args: string;
  result: string;
  latencyMs: number | null;
}) {
  const [open, setOpen] = useState(false);
  const parsed = toolName === "web_search" ? parseTavilyResult(result) : [];

  return (
    <>
      <tr
        className="border-t border-zinc-200 dark:border-zinc-800 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900"
        onClick={() => setOpen((o) => !o)}
      >
        <td className="px-3 py-2 w-8">{open ? "▾" : "▸"}</td>
        <td className="px-3 py-2">{idx + 1}</td>
        <td className="px-3 py-2">{toolName}</td>
        <td className="px-3 py-2 font-mono text-xs max-w-xl truncate" title={args}>{args}</td>
        <td className="px-3 py-2">{latencyMs != null ? `${latencyMs}ms` : "—"}</td>
      </tr>
      {open && (
        <tr className="border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
          <td colSpan={5} className="px-3 py-3">
            <div className="space-y-3">
              <div>
                <div className="text-xs text-zinc-500 mb-1">Args</div>
                <pre className="font-mono text-xs whitespace-pre-wrap">{args}</pre>
              </div>
              {parsed.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-xs text-zinc-500">Results ({parsed.length})</div>
                  {parsed.map((r, i) => (
                    <div key={i} className="border border-zinc-200 dark:border-zinc-800 rounded p-2 bg-white dark:bg-zinc-950">
                      <div className="text-sm font-medium">{r.title || "(no title)"}</div>
                      <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline break-all">{r.url}</a>
                      <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1 whitespace-pre-wrap line-clamp-6">{r.content}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Raw result</div>
                  <pre className="font-mono text-xs whitespace-pre-wrap max-h-96 overflow-auto">{result}</pre>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
