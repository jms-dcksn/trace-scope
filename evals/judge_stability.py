"""Judge stability check: run the judge N times on fixed agent outputs.

Pulls the "Last trial output" for cases 5, 6, 7, 9 from the most recent
results-*.md in results/, then scores each N times. If verdicts flip across
identical inputs, the judge itself is noisy — and flips you see during the
main eval may not be agent drift but judge drift.
"""
import re
import time
from pathlib import Path

from data import dataset, reference_output
from judge import CorrectnessJudge
from report import REPORTS_DIR, write_report

CASES = [5, 6, 7, 9]  # 1-indexed case numbers to re-score
TRIALS = 5


def _latest_results_file() -> Path | None:
    files = sorted(REPORTS_DIR.glob("results-*.md"))
    return files[-1] if files else None


def _parse_case_outputs(path: Path, case_nums: list[int]) -> dict[int, str]:
    """Extract the fenced 'Last trial output' block for each requested case."""
    text = path.read_text()
    # Split on case headers; keep header with its section.
    parts = re.split(r"(?m)^### Case (\d+) —", text)
    # parts = [preamble, "1", section1, "2", section2, ...]
    outputs: dict[int, str] = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        if n not in case_nums:
            continue
        section = parts[i + 1]
        m = re.search(
            r"\*\*Last trial output:\*\*\s*\n+```\n(.*?)\n```",
            section,
            re.DOTALL,
        )
        if m:
            outputs[n] = m.group(1)
    return outputs


async def run_judge_stability(trials: int = TRIALS) -> None:
    src = _latest_results_file()
    if src is None:
        print(f"No results-*.md found in {REPORTS_DIR}. Run a full eval first.")
        return
    print(f"Using outputs from {src.name}")

    outputs = _parse_case_outputs(src, CASES)
    missing = [n for n in CASES if n not in outputs]
    if missing:
        print(f"Could not parse outputs for case(s): {missing}")
        return

    judge = CorrectnessJudge()
    per_case: list[dict] = []
    start = time.perf_counter()

    for case_num in CASES:
        case = dataset[case_num - 1]
        output = outputs[case_num]
        ref = reference_output(case_num - 1)
        print(f"\n--- Case {case_num}: {case['input'][:80]} ---")
        verdicts, confidences, reasonings = [], [], []
        for t in range(trials):
            result = judge.evaluate(case["input"], output, case["criteria"], ref)
            label, confidence, reasoning = result.label, result.confidence, result.reasoning
            verdicts.append(label)
            confidences.append(confidence)
            reasonings.append(reasoning)
            print(f"[case {case_num} judge {t + 1}] {label} (conf {confidence}) — {reasoning}")
        pass_n = verdicts.count("pass")
        fail_n = verdicts.count("fail")
        agreement = max(pass_n, fail_n) / trials
        per_case.append({
            "case_num": case_num,
            "input": case["input"],
            "criteria": case["criteria"],
            "output": output,
            "verdicts": verdicts,
            "confidences": confidences,
            "reasonings": reasonings,
            "pass_n": pass_n,
            "fail_n": fail_n,
            "agreement": agreement,
        })

    elapsed = time.perf_counter() - start
    overall = sum(c["agreement"] for c in per_case) / len(per_case)
    stable = all(c["agreement"] == 1.0 for c in per_case)
    diagnosis = (
        "STABLE — judge is consistent across all cases; flips during eval reflect agent output drift"
        if stable
        else "UNSTABLE — judge itself is noisy on at least one case; flips aren't purely agent drift"
    )

    lines = [
        "# Judge Stability Check",
        "",
        "## Summary",
        "",
        f"- **Source:** {src.name}",
        f"- **Cases:** {', '.join(str(c) for c in CASES)}",
        f"- **Trials per case:** {trials} (judge calls only, fixed agent output)",
        f"- **Mean agreement:** {overall:.0%}",
        f"- **Diagnosis:** {diagnosis}",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Per-case agreement",
        "",
        "| Case | Pass | Fail | Agreement |",
        "|------|------|------|-----------|",
        *[
            f"| {c['case_num']} | {c['pass_n']} | {c['fail_n']} | {c['agreement']:.0%} |"
            for c in per_case
        ],
        "",
    ]

    for c in per_case:
        lines += [
            f"## Case {c['case_num']}",
            "",
            f"**Input:** {c['input']}",
            "",
            "**Judge criteria:**",
            "",
            *[f"{j + 1}. {crit}" for j, crit in enumerate(c["criteria"])],
            "",
            "**Fixed agent output:**",
            "",
            "```",
            c["output"],
            "```",
            "",
            "**Per-trial verdicts:**",
            "",
            "| Trial | Verdict | Confidence | Reasoning |",
            "|-------|---------|------------|-----------|",
            *[
                f"| {i + 1} | {v} | {conf} | {r.replace('|', '\\|')} |"
                for i, (v, conf, r) in enumerate(zip(c["verdicts"], c["confidences"], c["reasonings"]))
            ],
            "",
        ]

    summary = "\n".join(lines)
    print("\n\n" + summary)
    path = write_report("judge-check", summary)
    print(f"\nReport saved to {path.name}")
