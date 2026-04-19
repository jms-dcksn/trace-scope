"""CLI dispatcher for the agent-eval harness.

Usage:
    uv run main.py              # full eval: agent x dataset, scored by rule + judge
    uv run main.py judge-check  # judge stability check (judge-only, fixed output)
    uv run main.py judge-pr     # judge precision/recall on the golden dataset
"""
import asyncio
import sys

from evals.judge_precision_recall import run_judge_precision_recall
from evals.judge_stability import run_judge_stability
from evals.run_eval import run_dataset_eval


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == "judge-check":
        asyncio.run(run_judge_stability())
    elif cmd == "judge-pr":
        run_judge_precision_recall()
    else:
        asyncio.run(run_dataset_eval())


if __name__ == "__main__":
    main()
