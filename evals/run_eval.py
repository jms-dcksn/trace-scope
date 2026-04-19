"""Core eval: run the agent N times per case, score with rule + judge, report."""
import time
from pathlib import Path

from agent import SearchAgent
from data import dataset
from judge import Judge
from report import md_escape, timestamp, write_report

TRIALS = 3
CASE7_FIXTURE = Path(__file__).parent.parent / "case7_fixture.txt"


def _summarize(results: list[dict], elapsed: float) -> str:
    def sum_ratios(vals):
        num = den = 0
        for v in vals:
            a, _, b = v.partition("/")
            if a.isdigit() and b.isdigit():
                num += int(a); den += int(b)
        return num, den

    rule_pass, rule_total = sum_ratios([r["rule"] for r in results])
    judge_pass, judge_total = sum_ratios([r["judge"] for r in results])
    rule_avg = rule_pass / rule_total if rule_total else 0
    judge_avg = judge_pass / judge_total if judge_total else 0
    ts = timestamp()

    lines = [
        f"# Eval Report — {ts}",
        "",
        "## Summary",
        "",
        f"- **Trials per case:** {TRIALS}",
        f"- **Cases:** {len(results)}",
        f"- **Rule-based pass rate:** {rule_pass}/{rule_total} ({rule_avg:.0%})",
        f"- **LLM judge pass rate:** {judge_pass}/{judge_total} ({judge_avg:.0%})",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Per-case results",
        "",
        "| # | Difficulty | Rule | Judge | Input |",
        "|---|------------|------|-------|-------|",
    ]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        lines.append(
            f"| {i} | {difficulty} | {r['rule']} | {r['judge']} | {md_escape(r['input'])[:120]} |"
        )

    lines += ["", "## Case details", ""]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        lines += [
            f"### Case {i} — {difficulty} (rule {r['rule']}, judge {r['judge']})",
            "",
            f"**Input:** {r['input']}",
            "",
            "**Last trial output:**",
            "",
            "```",
            r["output"],
            "```",
            "",
            "**Judge criteria:**",
            "",
            *[f"{j + 1}. {c}" for j, c in enumerate(r["criteria"])],
            "",
            f"**Judge reasoning:** {r['judge_reasoning']}",
            "",
        ]
    return "\n".join(lines)


async def run_dataset_eval() -> None:
    agent = SearchAgent()
    await agent.setup()
    judge = Judge()
    results = []
    start = time.perf_counter()

    for idx, data in enumerate(dataset):
        print(f"\n--- {data['tags']} ---")
        print(f"Q: {data['input']}")
        rule_pass = judge_pass = rule_applicable = 0
        outputs, reasonings = [], []
        for t in range(TRIALS):
            output = await agent.ask(data["input"])
            print(f"[trial {t + 1}] {output}")
            outputs.append(output)
            if data.get("expected"):
                rule_applicable += 1
                if data["expected"] in output:
                    rule_pass += 1
            label, reasoning = judge.evaluate(data["input"], output, data["criteria"])
            print(f"[trial {t + 1}] judge: {label} — {reasoning}")
            reasonings.append(f"T{t + 1}: {reasoning}")
            if label == "pass":
                judge_pass += 1
        if idx == 6:
            CASE7_FIXTURE.write_text(outputs[-1])
        results.append({
            "input": data["input"],
            "output": outputs[-1],
            "tags": data["tags"],
            "criteria": data["criteria"],
            "rule": f"{rule_pass}/{rule_applicable}" if rule_applicable else "n/a",
            "judge": f"{judge_pass}/{TRIALS}",
            "judge_reasoning": " | ".join(reasonings),
        })

    summary = _summarize(results, time.perf_counter() - start)
    print("\n\n" + summary)
    path = write_report("results", summary)
    print(f"\nReport saved to {path.name}")
