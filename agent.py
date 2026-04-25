"""Agent under test: a Tavily-search-powered LangChain agent."""
import os
import time
from contextvars import ContextVar
from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain.tools import tool
from tavily import TavilyClient

from costs import cost_usd


SYSTEM_PROMPT = """You answer general questions using Tavily web search from public internet sources.
            You should cite your sources and include excerpts from cited sources to support and augment answers provided.
            The user needs to trust your answers and feel as though you have accurately researched their topic - so ensure
            you provide evidence from unbiased sources and avoid relying on your internal knowledge unless you are supremely confident.
            When comparing data, ensure you state any caveats or assumptions.
            Be precise and thorough in your responses.
            """


@dataclass
class SearchCall:
    query: str
    results: str
    latency_ms: int | None = None


@dataclass
class AgentRun:
    output: str
    evidence: list[SearchCall] = field(default_factory=list)
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None


# Per-ask call latency log: tool_call_id (or query if id missing) -> ms.
_tool_latencies: ContextVar[dict[str, int] | None] = ContextVar("_tool_latencies", default=None)
_tool_call_counter: ContextVar[int] = ContextVar("_tool_call_counter", default=0)

_tavily_client: TavilyClient | None = None


def _tavily() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return _tavily_client


@tool
def web_search(query: str) -> str:
    """Search the public web via Tavily and return top results with extracted page content."""
    t0 = time.perf_counter()
    response = _tavily().search(
        query=query,
        search_depth="advanced",
        max_results=8,
        include_answer=False,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    log = _tool_latencies.get()
    if log is not None:
        # Order-based key — _extract_evidence walks calls in order.
        idx = _tool_call_counter.get()
        _tool_call_counter.set(idx + 1)
        log[str(idx)] = elapsed_ms

    results = response.get("results") or []
    if not results:
        return "No web results found."
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')}"
        for r in results
    )


def _extract_evidence(messages: list, latencies: dict[str, int]) -> list[SearchCall]:
    """Pair each web_search tool_call with its ToolMessage result + recorded latency."""
    calls_by_id: dict[str, str] = {}
    call_order: list[str] = []
    for m in messages:
        for tc in getattr(m, "tool_calls", None) or []:
            if tc.get("name") == "web_search":
                calls_by_id[tc["id"]] = tc.get("args", {}).get("query", "")
                call_order.append(tc["id"])

    order_index = {tc_id: i for i, tc_id in enumerate(call_order)}
    evidence: list[SearchCall] = []
    for m in messages:
        tool_call_id = getattr(m, "tool_call_id", None)
        if tool_call_id and tool_call_id in calls_by_id:
            idx = order_index[tool_call_id]
            evidence.append(SearchCall(
                query=calls_by_id[tool_call_id],
                results=str(getattr(m, "content", "")),
                latency_ms=latencies.get(str(idx)),
            ))
    return evidence


def _sum_usage(messages: list) -> tuple[int | None, int | None]:
    """Sum input/output tokens across AIMessages with usage_metadata. None if absent."""
    tokens_in = tokens_out = 0
    seen = False
    for m in messages:
        usage = getattr(m, "usage_metadata", None)
        if not usage:
            continue
        seen = True
        tokens_in += usage.get("input_tokens", 0) or 0
        tokens_out += usage.get("output_tokens", 0) or 0
    return (tokens_in, tokens_out) if seen else (None, None)


class SearchAgent:
    """Wraps a LangChain agent that answers questions via Tavily web search."""

    def __init__(self, model: str = "openai:gpt-5.4-mini"):
        self.model = model
        self._agent = None

    async def setup(self) -> None:
        self._agent = create_agent(
            model=self.model,
            tools=[web_search],
            system_prompt=SYSTEM_PROMPT,
        )

    async def ask(self, query: str) -> AgentRun:
        if self._agent is None:
            raise RuntimeError("Call setup() before ask().")

        latencies: dict[str, int] = {}
        token_l = _tool_latencies.set(latencies)
        token_c = _tool_call_counter.set(0)
        t0 = time.perf_counter()
        try:
            result = await self._agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        finally:
            _tool_latencies.reset(token_l)
            _tool_call_counter.reset(token_c)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        messages = result["messages"]
        tokens_in, tokens_out = _sum_usage(messages)
        return AgentRun(
            output=messages[-1].content,
            evidence=_extract_evidence(messages, latencies),
            latency_ms=elapsed_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd(self.model, tokens_in, tokens_out),
        )
