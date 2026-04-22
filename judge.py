"""LLM-as-judge: scores an agent response per-criterion.

Each criterion gets its own pass/fail + confidence + reasoning. The overall
case label is pass iff every criterion passes. Structured so a second judge
(e.g. faithfulness) can subclass BaseJudge and only override name + prompt.
"""
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


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
        self._llm = ChatOpenAI(
            model=model,
            temperature=0,
        ).with_structured_output(JudgeVerdict)

    def build_prompt(self, **kwargs) -> str:
        raise NotImplementedError

    def _parse(self, criteria: list[str], verdict: JudgeVerdict | None) -> JudgeResult:
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
        return JudgeResult(results)


class CorrectnessJudge(BaseJudge):
    """Scores output correctness against the supplied criteria."""

    name = "correctness"

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
        verdict = self._llm.invoke(
            self.build_prompt(agent_input, agent_output, criteria, reference_output)
        )
        return self._parse(criteria, verdict)
