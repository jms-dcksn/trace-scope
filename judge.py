"""LLM-as-judge: scores an agent response per-criterion.

Each criterion gets its own pass/fail + confidence + reasoning. The overall
case label is pass iff every criterion passes. Structured so a second judge
(e.g. faithfulness) can subclass BaseJudge and only override name + prompt.
"""
import time
from dataclasses import dataclass, field
from datetime import datetime

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from costs import cost_usd


class CriterionVerdict(BaseModel):
    index: int  # 1-based, matches the numbered criterion in the prompt
    score: int  # 1 = pass, 0 = fail
    confidence: int  # 0-100
    reasoning: str


class JudgeVerdict(BaseModel):
    verdicts: list[CriterionVerdict]


@dataclass
class CriterionResult:
    criterion: str
    label: str  # pass | fail | unknown
    confidence: int
    reasoning: str


@dataclass
class JudgeResult:
    per_criterion: list[CriterionResult]
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None

    @property
    def label(self) -> str:
        if not self.per_criterion:
            return "unknown"
        if any(c.label == "unknown" for c in self.per_criterion):
            return "unknown"
        return "pass" if all(c.label == "pass" for c in self.per_criterion) else "fail"

    @property
    def confidence(self) -> int:
        # Overall confidence = weakest link.
        return min((c.confidence for c in self.per_criterion), default=0)

    @property
    def reasoning(self) -> str:
        return " | ".join(
            f"[{i + 1}] {c.label}: {c.reasoning}"
            for i, c in enumerate(self.per_criterion)
        )


class BaseJudge:
    """Shared LLM invocation + per-criterion parsing. Subclasses supply a prompt."""

    name: str = "base"

    def __init__(self, model: str = "gpt-5.4"):
        self.model = model
        # include_raw=True so we can read usage_metadata for token/cost accounting.
        self._llm = ChatOpenAI(
            model=model,
            temperature=0,
        ).with_structured_output(JudgeVerdict, include_raw=True)

    def build_prompt(self, **kwargs) -> str:
        raise NotImplementedError

    def _invoke(self, prompt: str) -> tuple[JudgeVerdict | None, dict]:
        """Run the LLM. Returns (parsed_verdict, metrics)."""
        t0 = time.perf_counter()
        response = self._llm.invoke(prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        raw = response.get("raw") if isinstance(response, dict) else None
        parsed = response.get("parsed") if isinstance(response, dict) else response
        usage = getattr(raw, "usage_metadata", None) or {}
        tokens_in = usage.get("input_tokens")
        tokens_out = usage.get("output_tokens")
        return parsed, {
            "latency_ms": elapsed_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd(self.model, tokens_in, tokens_out),
        }

    def _parse(self, criteria: list[str], verdict: JudgeVerdict | None, metrics: dict | None = None) -> JudgeResult:
        by_idx = {v.index: v for v in (verdict.verdicts if verdict else [])}
        results: list[CriterionResult] = []
        for i, c in enumerate(criteria, 1):
            v = by_idx.get(i)
            if v is None:
                results.append(CriterionResult(c, "unknown", 0, ""))
                continue
            conf = max(0, min(100, v.confidence))
            if v.score == 1:
                label = "pass"
            elif v.score == 0:
                label = "fail"
            else:
                label = "unknown"
            results.append(CriterionResult(c, label, conf, v.reasoning))
        m = metrics or {}
        return JudgeResult(
            results,
            latency_ms=m.get("latency_ms"),
            tokens_in=m.get("tokens_in"),
            tokens_out=m.get("tokens_out"),
            cost_usd=m.get("cost_usd"),
        )


class CorrectnessJudge(BaseJudge):
    """Scores output correctness against the supplied criteria."""

    name = "correctness"
    # Bump manually when the prompt changes — config_hash depends on this.
    PROMPT_VERSION = "v1"

    def build_prompt(
        self,
        agent_input: str,
        agent_output: str,
        criteria: list[str],
        reference_output: str | None = None,
    ) -> str:
        numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(criteria))
        reference_section = ""
        if reference_output:
            reference_section = f'''
Reference output (an example of a correct, high-quality response to this
input — treat as a guide to what "correct" looks like, not the only valid
phrasing; the agent response does not need to match it verbatim):
"""
{reference_output}
"""
'''
        return f'''
The current date is {datetime.now().isoformat(timespec='seconds')}.
You are judging the correctness of an agent response against a list of
criteria. Evaluate each criterion independently.

Criteria:
{numbered}

Agent input:
"""
{agent_input}
"""

Agent response:
"""
{agent_output}
"""
{reference_section}
For each criterion, return an entry in "verdicts" with:
- "index": the 1-based criterion number
- "score": 1 for PASS, 0 for FAIL
- "confidence": integer 0-100 (100 = supremely confident, 0 = pure guess)
- "reasoning": one-sentence justification

Return exactly one verdict per criterion.
'''

    def evaluate(
        self,
        agent_input: str,
        agent_output: str,
        criteria: list[str],
        reference_output: str | None = None,
    ) -> JudgeResult:
        verdict, metrics = self._invoke(
            self.build_prompt(agent_input, agent_output, criteria, reference_output)
        )
        return self._parse(criteria, verdict, metrics)


FAITHFULNESS_CRITERION = "The response is grounded in the retrieved evidence."


def render_trace(evidence: list) -> str:
    """The trace string shown to the faithfulness judge — also persisted to traces."""
    if not evidence:
        return "(no searches were performed)"
    return "\n\n".join(
        f"[search {i + 1}] query: {e.query}\n{e.results}"
        for i, e in enumerate(evidence)
    )


class FaithfulnessJudge(BaseJudge):
    """Single pass/fail verdict on whether the response is grounded in evidence."""

    name = "faithfulness"
    PROMPT_VERSION = "v1"
    criteria = [FAITHFULNESS_CRITERION]

    def build_prompt(
        self,
        agent_input: str,
        agent_output: str,
        evidence: list,  # list[SearchCall]
    ) -> str:
        evidence_block = render_trace(evidence)
        return f'''
The current date is {datetime.now().isoformat(timespec='seconds')}.
You are judging whether an agent response is FAITHFUL to the evidence it
retrieved from web search. Evidence is AUTHORITATIVE for grounding: if a
material claim in the response does not appear in the evidence, the
response is not grounded, regardless of whether the claim is true in the
world. Do not use your own background knowledge to confirm or refute
claims. Fabricated quotes, unsupported statute/bill numbers, and
citations that do not appear in the evidence all fail this check.

Agent input:
"""
{agent_input}
"""

Agent response:
"""
{agent_output}
"""

Retrieved evidence (all tool calls the agent made, in order):
"""
{evidence_block}
"""

Return a single verdict with:
- "index": 1
- "score": 1 for PASS (response is grounded in evidence), 0 for FAIL
- "confidence": integer 0-100 (100 = supremely confident, 0 = pure guess)
- "reasoning": one-sentence justification, citing which search result supports or contradicts
'''

    def evaluate(
        self,
        agent_input: str,
        agent_output: str,
        evidence: list,
    ) -> JudgeResult:
        verdict, metrics = self._invoke(
            self.build_prompt(agent_input, agent_output, evidence)
        )
        return self._parse(self.criteria, verdict, metrics)
