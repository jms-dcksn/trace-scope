"""Core eval: run the agent N times per case, score with rule + judge, report."""
import asyncio
import time

from agent import SearchAgent
from data import dataset, reference_output
from judge import CorrectnessJudge
from report import md_escape, timestamp, write_report

TRIALS = 3
BRAVE_RATE_LIMIT_DELAY = 1.1  # Brave free tier ≈ 1 req/sec


def _summarize(results: list[dict], elapsed: float) -> str:
    rule_pass = sum(r["rule_pass"] for r in results)
    rule_total = sum(r["rule_total"] for r in results)
    case_pass = sum(r["judge_pass"] for r in results)
    case_total = sum(r["judge_total"] for r in results)
    crit_pass = sum(sum(c["pass_n"] for c in r["criteria_stats"]) for r in results)
    crit_total = sum(sum(c["total"] for c in r["criteria_stats"]) for r in results)

    rule_avg = rule_pass / rule_total if rule_total else 0
    case_avg = case_pass / case_total if case_total else 0
    crit_avg = crit_pass / crit_total if crit_total else 0
    ts = timestamp()

    lines = [
        f"# Eval Report — {ts}",
        "",
        "## Summary",
        "",
        f"- **Trials per case:** {TRIALS}",
        f"- **Cases:** {len(results)}",
        f"- **Rule-based pass rate:** {rule_pass}/{rule_total} ({rule_avg:.0%})",
        f"- **Judge case pass rate (all criteria pass):** {case_pass}/{case_total} ({case_avg:.0%})",
        f"- **Judge per-criterion pass rate:** {crit_pass}/{crit_total} ({crit_avg:.0%})",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Per-case results",
        "",
        "| # | Difficulty | Rule | Case pass | Criteria pass | Input |",
        "|---|------------|------|-----------|---------------|-------|",
    ]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        rule = f"{r['rule_pass']}/{r['rule_total']}" if r["rule_total"] else "n/a"
        case_ratio = f"{r['judge_pass']}/{r['judge_total']}"
        crit_p = sum(c["pass_n"] for c in r["criteria_stats"])
        crit_t = sum(c["total"] for c in r["criteria_stats"])
        lines.append(
            f"| {i} | {difficulty} | {rule} | {case_ratio} | {crit_p}/{crit_t} | {md_escape(r['input'])[:120]} |"
        )

    lines += ["", "## Case details", ""]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        rule = f"{r['rule_pass']}/{r['rule_total']}" if r["rule_total"] else "n/a"
        lines += [
            f"### Case {i} — {difficulty} (rule {rule}, case pass {r['judge_pass']}/{r['judge_total']})",
            "",
            f"**Input:** {r['input']}",
            "",
            "**Last trial output:**",
            "",
            "```",
            r["output"],
            "```",
            "",
            "**Per-criterion pass rates:**",
            "",
            "| # | Criterion | Pass rate |",
            "|---|-----------|-----------|",
            *[
                f"| {j + 1} | {md_escape(c['criterion'])} | {c['pass_n']}/{c['total']} |"
                for j, c in enumerate(r["criteria_stats"])
            ],
            "",
            f"**Judge reasoning:** {r['judge_reasoning']}",
            "",
        ]
    return "\n".join(lines)


async def run_dataset_eval() -> None:
    agent = SearchAgent()
    await agent.setup()
    judge = CorrectnessJudge()
    results = []
    start = time.perf_counter()

    for idx, data in enumerate(dataset):
        print(f"\n--- {data['tags']} ---")
        print(f"Q: {data['input']}")
        rule_pass = rule_total = judge_pass = 0
        outputs, reasonings = [], []
        criteria_stats = [
            {"criterion": c, "pass_n": 0, "total": 0} for c in data["criteria"]
        ]
        ref = reference_output(idx)

        for t in range(TRIALS):
            if t > 0:
                await asyncio.sleep(BRAVE_RATE_LIMIT_DELAY)
            output = await agent.ask(data["input"])
            print(f"[trial {t + 1}] {output}")
            outputs.append(output)
            if data.get("expected"):
                rule_total += 1
                if data["expected"] in output:
                    rule_pass += 1
            result = judge.evaluate(data["input"], output, data["criteria"], ref)
            print(f"[trial {t + 1}] judge: {result.label} (conf {result.confidence})")
            for j, cr in enumerate(result.per_criterion):
                criteria_stats[j]["total"] += 1
                if cr.label == "pass":
                    criteria_stats[j]["pass_n"] += 1
                print(f"    [{j + 1}] {cr.label} (conf {cr.confidence}) — {cr.reasoning}")
            reasonings.append(
                f"T{t + 1} ({result.label}, conf {result.confidence}): {result.reasoning}"
            )
            if result.label == "pass":
                judge_pass += 1

        results.append({
            "input": data["input"],
            "output": outputs[-1],
            "tags": data["tags"],
            "criteria": data["criteria"],
            "rule_pass": rule_pass,
            "rule_total": rule_total,
            "judge_pass": judge_pass,
            "judge_total": TRIALS,
            "criteria_stats": criteria_stats,
            "judge_reasoning": " || ".join(reasonings),
        })

    summary = _summarize(results, time.perf_counter() - start)
    print("\n\n" + summary)
    path = write_report("results", summary)
    print(f"\nReport saved to {path.name}")
