"""Agent under test: a Brave-search-powered LangChain agent."""
import os
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


class SearchAgent:
    """Wraps a LangChain agent that answers questions via Brave web search."""

    def __init__(self, model: str = "openai:gpt-5.4-mini"):
        self.model = model
        self._client = MultiServerMCPClient(
            {
                "brave": {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
                    "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")},
                }
            }
        )
        self._agent = None

    async def setup(self) -> None:
        tools = await self._client.get_tools()
        self._agent = create_agent(
            model=self.model,
            tools=tools,
            system_prompt="You answer general questions using Brave web search from public internet sources.",
        )

    async def ask(self, query: str) -> str:
        if self._agent is None:
            raise RuntimeError("Call setup() before ask().")
        result = await self._agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content
