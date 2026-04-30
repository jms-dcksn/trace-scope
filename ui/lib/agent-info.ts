export const AGENT_SYSTEM_PROMPT = `You answer general questions using Tavily web search from public internet sources.
            You should cite your sources and include excerpts from cited sources to support and augment answers provided.
            The user needs to trust your answers and feel as though you have accurately researched their topic - so ensure
            you provide evidence from unbiased sources and avoid relying on your internal knowledge unless you are supremely confident.
            When comparing data, ensure you state any caveats or assumptions.
            Be precise and thorough in your responses.
            `;

export type AgentTool = {
  name: string;
  description: string;
  parameters: { name: string; type: string; description: string }[];
};

export const AGENT_TOOLS: AgentTool[] = [
  {
    name: "web_search",
    description: "Search the public web via Tavily and return top results with extracted page content.",
    parameters: [{ name: "query", type: "string", description: "The search query string." }],
  },
];

export const AGENT_DEFAULT_MODEL = "openai:gpt-5.4-mini";
