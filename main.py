"""CLI dispatcher for the agent-eval harness.

Usage:
    uv run main.py              # full eval: agent x dataset, scored by rule + judge
    uv run main.py 3-5-7        # run only dataset cases 3, 5, 7 (1-indexed)
    uv run main.py judge-check  # judge stability check (judge-only, fixed output)
    uv run main.py judge-pr     # judge precision/recall on the golden dataset
"""
import asyncio
import sys

from data import dataset
from evals.judge_precision_recall import run_judge_precision_recall
from evals.judge_stability import run_judge_stability
from evals.run_eval import run_dataset_eval


def _parse_indices(arg: str) -> list[int]:
    indices = [int(p) - 1 for p in arg.split("-") if p]
    for i in indices:
        if i < 0 or i >= len(dataset):
            raise SystemExit(f"Index {i + 1} out of range (1..{len(dataset)})")
    return indices


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == "judge-check":
        asyncio.run(run_judge_stability())
    elif cmd == "judge-pr":
        run_judge_precision_recall()
    elif cmd:
        asyncio.run(run_dataset_eval(_parse_indices(cmd)))
    else:
        asyncio.run(run_dataset_eval())


if __name__ == "__main__":
    main()
