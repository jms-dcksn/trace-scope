"""Judge stability check: run the judge N times on a fixed agent output.

If verdicts flip across identical inputs, the judge itself is noisy — and
flips you see during the main eval may not be agent drift but judge drift.
"""
import time

from data import dataset
from judge import Judge
from report import write_report
from evals.run_eval import CASE7_FIXTURE


async def run_judge_stability(trials: int = 5) -> None:
    case = dataset[6]
    if not CASE7_FIXTURE.exists():
        print(f"No fixture at {CASE7_FIXTURE}. Run a full eval first to capture one.")
        return

    output = CASE7_FIXTURE.read_text()
    judge = Judge()
    verdicts, reasonings = [], []
    start = time.perf_counter()
    for t in range(trials):
        label, reasoning = judge.evaluate(case["input"], output, case["criteria"])
        verdicts.append(label); reasonings.append(reasoning)
        print(f"[judge {t + 1}] {label} — {reasoning}")
    elapsed = time.perf_counter() - start

    pass_n, fail_n = verdicts.count("pass"), verdicts.count("fail")
    agreement = max(pass_n, fail_n) / trials
    diagnosis = (
        "STABLE — judge is consistent; flips during eval reflect agent output drift"
        if agreement == 1.0
        else "UNSTABLE — judge itself is noisy; flips aren't just agent drift"
    )

    lines = [
        "# Judge Stability Check",
        "",
        "## Summary",
        "",
        f"- **Case:** 7 — {case['input']}",
        f"- **Trials:** {trials} (judge calls only, fixed agent output)",
        f"- **Verdicts:** pass={pass_n}, fail={fail_n}",
        f"- **Agreement:** {agreement:.0%}",
        f"- **Diagnosis:** {diagnosis}",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Judge criteria",
        "",
        *[f"{j + 1}. {c}" for j, c in enumerate(case["criteria"])],
        "",
        "## Fixed agent output",
        "",
        "```",
        output,
        "```",
        "",
        "## Per-trial verdicts",
        "",
        "| Trial | Verdict | Reasoning |",
        "|-------|---------|-----------|",
        *[f"| {i + 1} | {v} | {r.replace('|', '\\|')} |"
          for i, (v, r) in enumerate(zip(verdicts, reasonings))],
        "",
    ]
    summary = "\n".join(lines)
    print("\n\n" + summary)
    path = write_report("judge-check", summary)
    print(f"\nReport saved to {path.name}")
