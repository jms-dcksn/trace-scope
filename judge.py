"""LLM-as-judge: scores an agent response against a list of criteria."""
from datetime import datetime
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    score: int
    reasoning: str


class Judge:
    """An LLM-as-judge that returns pass/fail with reasoning."""

    def __init__(self, model: str = "gpt-5.4"):
        self.model = model
        self._llm = ChatOpenAI(
            model=model,
            use_responses_api=True,
            output_version="responses/v1",
        ).with_structured_output(JudgeVerdict)

    @staticmethod
    def build_prompt(agent_input: str, agent_output: str, criteria: list[str]) -> str:
        numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(criteria))
        return f'''
The current date is {datetime.now().isoformat(timespec='seconds')}.
Evaluate the final response from the agent based on the following criteria:
{numbered}

Agent input:
"""
{agent_input}
"""

Agent response:
"""
{agent_output}
"""

Set "score" to 1 for PASS or 0 for FAIL, and "reasoning" to a one-sentence justification.
'''

    @staticmethod
    def parse(verdict: JudgeVerdict | None) -> tuple[str, str]:
        if verdict is None:
            return "unknown", ""
        if verdict.score == 1:
            return "pass", verdict.reasoning
        if verdict.score == 0:
            return "fail", verdict.reasoning
        return "unknown", verdict.reasoning

    def evaluate(self, agent_input: str, agent_output: str, criteria: list[str]) -> tuple[str, str]:
        verdict = self._llm.invoke(self.build_prompt(agent_input, agent_output, criteria))
        return self.parse(verdict)
