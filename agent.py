"""Agent under test: a Brave-search-powered LangChain agent."""
import os

import requests
from langchain.agents import create_agent
from langchain.tools import tool

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

@tool
def brave_search(query: str) -> str:
    """Search the public web via Brave and return the top results as text."""
    response = requests.get(
        BRAVE_SEARCH_URL,
        params={"q": query, "count": 10},
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": os.environ["BRAVE_API_KEY"],
        },
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("web", {}).get("results", []) or []
    if not results:
        return "No web results found."
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('description', '')}"
        for r in results
    )


class SearchAgent:
    """Wraps a LangChain agent that answers questions via Brave web search."""

    def __init__(self, model: str = "openai:gpt-5.4-mini"):
        self.model = model
        self._agent = None

    async def setup(self) -> None:
        self._agent = create_agent(
            model=self.model,
            tools=[brave_search],
            system_prompt="""You answer general questions using Brave web search from public internet sources. 
            You should cite your sources and include excerpts from cited sources to support and augment answers provided.
            The user needs to trust your answers and feel as though you have accurately researched their topic - so ensure 
            you provide evidence from unbiased sources and avoid relying on your internal knowledge unless you are supremely confident.
            Be precise and thorough in your responses.
            """,
        )

    async def ask(self, query: str) -> str:
        if self._agent is None:
            raise RuntimeError("Call setup() before ask().")
        result = await self._agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content
