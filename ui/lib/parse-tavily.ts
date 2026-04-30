export type TavilyResult = { title: string; url: string; content: string };

// Format produced by agent.py:web_search:
//   "{title}\n{url}\n{content}\n\n{title}\n{url}\n{content}\n\n..."
// Or the literal "No web results found."
export function parseTavilyResult(raw: string): TavilyResult[] {
  if (!raw || raw.trim() === "No web results found.") return [];
  const blocks = raw.split(/\n\n+/);
  const out: TavilyResult[] = [];
  for (const block of blocks) {
    const lines = block.split("\n");
    if (lines.length < 2) continue;
    const [title, url, ...rest] = lines;
    out.push({ title, url, content: rest.join("\n") });
  }
  return out;
}
