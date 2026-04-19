import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    score: int
    reasoning: str


def judge_model(model: str = "gpt-5.4"):
    return ChatOpenAI(
        model=model,
        use_responses_api=True,
        output_version="responses/v1",
    ).with_structured_output(JudgeVerdict)


dataset = [
    # --- Simple ---
    {
        "input": "What's the capital of France?",
        "expected": "Paris",
        "criteria": [
            "mentions Paris",
            "doesn't hallucinate other cities as the capital",
        ],
        "tags": ["factual", "simple"],
    },
    {
        "input": "Who wrote the novel 1984?",
        "expected": "George Orwell",
        "criteria": [
            "mentions George Orwell",
            "doesn't attribute the book to another author",
        ],
        "tags": ["factual", "simple"],
    },
    {
        "input": "What is the chemical symbol for gold?",
        "expected": "Au",
        "criteria": [
            "identifies the symbol as Au",
            "doesn't confuse with silver (Ag) or other elements",
        ],
        "tags": ["factual", "simple"],
    },

    # --- Medium ---
    {
        "input": "Which company acquired GitHub and in what year?",
        "expected": "Microsoft",
        "criteria": [
            "identifies Microsoft as the acquirer",
            "states the year as 2018",
            "optionally mentions the ~$7.5B deal value accurately",
        ],
        "tags": ["factual", "medium"],
    },
    {
        "input": "What is the current population of Tokyo, and how has it changed over the last decade?",
        "expected": None,
        "criteria": [
            "cites a recent population figure for Tokyo (city or metro, stated clearly)",
            "describes the trend observed in population",
            "cites or references a credible source",
        ],
        "tags": ["research", "medium"],
    },
    {
        "input": "Compare the battery range of the 2024 Tesla Model 3 Long Range vs the 2024 Hyundai Ioniq 6 Long Range.",
        "expected": None,
        "criteria": [
            "provides an EPA range figure for each vehicle",
            "correctly identifies which has the longer range",
            "doesn't confuse trims or model years",
        ],
        "tags": ["comparison", "medium"],
    },

    # --- Super tough ---
    {
        "input": "Summarize the key findings of the most recent IPCC Synthesis Report and identify two specific policy recommendations it makes for the financial sector.",
        "expected": None,
        "criteria": [
            "correctly identifies the AR6 Synthesis Report (2023) or newer if available",
            "accurately summarizes at least two key scientific findings",
            "cites two specific, real policy recommendations relevant to finance",
            "does not fabricate recommendations or conflate with other reports",
        ],
        "tags": ["research", "hard"],
    },
    {
        "input": (
            "A mid-size US insurer wants to deploy an agentic AI system for claims triage. "
            "What are the top 3 regulatory considerations they should address in 2026, "
            "citing specific state or federal guidance?"
        ),
        "expected": None,
        "criteria": [
            "cites regulatory sources",
            "top considerations are substantive (bias testing, explainability, governance, consumer disclosure)",
            "answer is scoped to US insurance, not generic AI regulation",
        ],
        "tags": ["domain", "regulatory", "hard"],
    },
    {
        "input": (
            "Identify three publicly traded companies whose most recent 10-K explicitly discloses "
            "material risk from generative AI to their core business model, and quote the relevant risk factor language."
        ),
        "expected": None,
        "criteria": [
            "names three publicly traded companies",
            "each citation references a 10-K filing (year identified)",
            "risk described is genuinely about generative AI threatening the business, not generic tech risk",
        ],
        "tags": ["research", "financial", "hard"],
    },
]


def build_judge_prompt(agent_input: str, agent_output: str, criteria: list[str]) -> str:
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


def parse_judge_verdict(verdict: JudgeVerdict | None) -> tuple[str, str]:
    if verdict is None:
        return "unknown", ""
    if verdict.score == 1:
        return "pass", verdict.reasoning
    if verdict.score == 0:
        return "fail", verdict.reasoning
    return "unknown", verdict.reasoning


def print_summary(results: list[dict], elapsed: float) -> None:
    def md_escape(s: str) -> str:
        return s.replace("|", "\\|").replace("\n", " ")

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
    timestamp = datetime.now().isoformat(timespec="seconds")

    lines = [
        f"# Eval Report — {timestamp}",
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

    summary = "\n".join(lines)
    print("\n\n" + summary)

    out_path = Path(__file__).parent / f"results-{timestamp.replace(':', '-')}.md"
    out_path.write_text(summary + "\n")
    print(f"\nReport saved to {out_path.name}")


mcp_client = MultiServerMCPClient(
    {
        "brave": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
            "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")},
        }
    }
)


async def build_agent():
    tools = await mcp_client.get_tools()
    return create_agent(
        model="openai:gpt-5.4-mini",
        tools=tools,
        system_prompt="You answer general questions using Brave web search from public internet sources.",
    )


async def run_agent(agent, query: str) -> str:
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


TRIALS = 3
CASE7_FIXTURE = Path(__file__).parent / "case7_fixture.txt"


# --- Golden dataset ---
# Hand-annotated (input, output, gold_label) triples used to measure
# the judge's precision and recall. Outputs are sampled from real runs
# (see results-archive.txt). gold_label is my own verdict on whether
# the output meets the criteria — it does NOT always agree with the
# judge's historical verdict; the disagreements are the point.
golden_dataset = [
    # ---- Case 1: simple factual ----
    {
        "case_idx": 0,
        "output": "The capital of France is **Paris**.",
        "gold_label": "pass",
        "notes": "Trivially correct.",
    },
    {
        "case_idx": 0,
        "output": "The capital of France is Lyon.",
        "gold_label": "fail",
        "notes": "Synthetic negative — wrong city, judge must catch this.",
    },

    # ---- Case 2: 1984 author ----
    {
        "case_idx": 1,
        "output": "*1984* was written by **George Orwell**.",
        "gold_label": "pass",
        "notes": "Correct author.",
    },
    {
        "case_idx": 1,
        "output": "*1984* was written by Aldous Huxley, best known for Brave New World.",
        "gold_label": "fail",
        "notes": "Synthetic negative — wrong author.",
    },

    # ---- Case 3: chemical symbol for gold ----
    {
        "case_idx": 2,
        "output": "The chemical symbol for gold is **Au**.",
        "gold_label": "pass",
        "notes": "Correct symbol.",
    },

    # ---- Case 4: GitHub acquisition ----
    {
        "case_idx": 3,
        "output": (
            "GitHub was acquired by **Microsoft** in **2018** for approximately "
            "$7.5 billion in stock."
        ),
        "gold_label": "pass",
        "notes": "All three optional details correct.",
    },

    # ---- Case 5: Tokyo population ----
    {
        "case_idx": 4,
        "output": (
            "Tokyo's population is **about 14.19 million** as of 2024 (Tokyo "
            "Metropolitan Government: 14,192,184). Over the last decade it has "
            "grown modestly: ~13.48M in 2014, 14.065M in the 2020 census, "
            "14.19M in 2024 — roughly 5% growth. Sources: Tokyo Metropolitan "
            "Government and Japan Statistics Bureau."
        ),
        "gold_label": "pass",
        "notes": "Recent figure, clear trend, credible sources cited.",
    },
    {
        "case_idx": 4,
        "output": (
            "Tokyo's current population is about 14.19 million (Tokyo "
            "Metropolitan Government, 2024). Over the last decade Tokyo's "
            "population has been remarkably stable, with only modest growth "
            "rather than dramatic increase or decline."
        ),
        "gold_label": "pass",
        "notes": (
            "Judge marked this FAIL in archive (claimed trend should be flat/"
            "decline). Disagree — criteria only require *describing* the trend "
            "and citing a source, both done. The kind of false negative the "
            "precision/recall measurement should expose."
        ),
    },

    # ---- Case 6: Tesla Model 3 vs Ioniq 6 range ----
    {
        "case_idx": 5,
        "output": (
            "**2024 Tesla Model 3 Long Range:** EPA 363 mi (RWD) / 346 mi "
            "(AWD).\n**2024 Hyundai Ioniq 6 SE Long Range:** EPA 361 mi "
            "(RWD) / 316 mi (AWD).\n\nLike-for-like, the Tesla wins both: "
            "+2 mi RWD vs RWD, +30 mi AWD vs AWD."
        ),
        "gold_label": "pass",
        "notes": (
            "Judge marked similar outputs FAIL in archive for 'mixing trims', "
            "but the answer explicitly distinguishes RWD/AWD and does a "
            "like-for-like comparison. Another likely judge false negative."
        ),
    },

    # ---- Case 7: IPCC Synthesis Report ----
    {
        "case_idx": 6,
        "output": (
            "The most recent IPCC Synthesis Report is the **AR6 Synthesis "
            "Report: Climate Change 2023**.\n\nKey findings: (1) human "
            "influence on climate is unequivocal; warming, sea-level rise and "
            "extreme events are already affecting people and ecosystems; "
            "(2) impacts and risks rise with every increment of warming and "
            "some losses are already unavoidable; (3) strong, rapid, sustained "
            "emissions cuts this decade are essential to keep 1.5°C in reach; "
            "(4) adaptation is uneven and underfunded, and current financial "
            "flows fall short of mitigation/adaptation needs.\n\nTwo "
            "finance-sector policy recommendations: (a) align public finances "
            "and government signals to lower regulatory, cost and market "
            "barriers, redirecting capital toward climate action; "
            "(b) financial actors — investors, intermediaries, central banks, "
            "and regulators — should address the systemic underpricing of "
            "climate-related risks and close the gap between available capital "
            "and climate investment needs."
        ),
        "gold_label": "pass",
        "notes": "Correctly identifies AR6 (2023), real findings, real finance recs.",
    },

    # ---- Case 8: US insurer regulatory considerations ----
    {
        "case_idx": 7,
        "output": (
            "Top 3 regulatory considerations for a mid-size US insurer "
            "deploying agentic AI for claims triage in 2026:\n\n"
            "1. **Unfair discrimination / bias in claims decisions.** NY DFS "
            "Circular Letter No. 7 (2024) requires insurers to manage AI/"
            "predictive models in compliance with anti-discrimination law and "
            "forbids relying solely on a vendor's non-discrimination claim. "
            "Colorado SB24-205 imposes 'reasonable care' duties on high-risk "
            "AI systems.\n"
            "2. **Claims-handling and unfair claims settlement practices.** "
            "Triage that affects routing, prioritization or payment timing is "
            "subject to state unfair claims practices laws and the NAIC AI "
            "Model Bulletin (Dec 2023), which requires a written AI governance "
            "program proportionate to risk.\n"
            "3. **Governance, documentation and exam readiness.** The NAIC "
            "Model Bulletin and NAIC's developing AI Systems Evaluation Tool "
            "expect insurers to demonstrate testing, monitoring, vendor "
            "oversight and human override; NYDFS may audit AI use directly."
        ),
        "gold_label": "pass",
        "notes": "Cites real US insurance authorities, substantive, properly scoped.",
    },
    {
        "case_idx": 7,
        "output": (
            "Insurers deploying AI should consider the EU AI Act's high-risk "
            "classification rules, GDPR data minimization requirements, and "
            "the OECD AI Principles on transparency and accountability. They "
            "should also follow general best practices like having a human in "
            "the loop and conducting model reviews."
        ),
        "gold_label": "fail",
        "notes": (
            "Out of scope (EU/GDPR/OECD instead of US insurance), no US state "
            "or federal insurance guidance cited. Should be a clear FAIL."
        ),
    },

    # ---- Case 9: 10-K generative AI risk factors ----
    {
        "case_idx": 8,
        "output": (
            "Three publicly traded companies whose most recent 10-Ks disclose "
            "material generative-AI risk to their core business:\n\n"
            "1. **Manhattan Associates (NASDAQ: MANH)** — 10-K for FY2024: "
            "'Generative AI features embedded in our software products may "
            "create incomplete or inaccurate outputs and this could result in "
            "customer dissatisfaction or potential claims related to product "
            "performance.'\n"
            "2. **Gen Digital (NASDAQ: GEN)** — 10-K for FY2025: 'there is a "
            "risk of employees inadvertently inputting trade secret information "
            "into Gen AI technologies, thereby enabling third parties, "
            "including our competitors, to access such information.'\n"
            "3. **Veritone (NASDAQ: VERI)** — 10-K for FY2024: 'Issues in the "
            "use of AI (including machine learning) in our platforms may result "
            "in reputational harm or liability.'"
        ),
        "gold_label": "fail",
        "notes": (
            "Real companies with plausible quotes, but Gen Digital's quote is "
            "employee-leak risk (generic infosec, not a gen-AI threat to the "
            "business model) and Veritone's is generic AI reliability. Two of "
            "three fail the 'genuinely about generative AI threatening the "
            "business' criterion. Agree with archive: FAIL."
        ),
    },
    {
        "case_idx": 8,
        "output": (
            "Several companies disclose AI-related risks. For example, many "
            "tech firms have added language about artificial intelligence to "
            "their risk factors in recent annual reports, noting that AI could "
            "disrupt their business or expose them to new competitive threats. "
            "Specific names and quotes vary by filing."
        ),
        "gold_label": "fail",
        "notes": "No company names, no quotes, no filing years. Clear FAIL.",
    },
]


def run_judge_pr(model: str = "gpt-5.4") -> None:
    """Run the judge on the golden dataset; report precision/recall."""
    tp = fp = tn = fn = 0
    rows = []
    start = time.perf_counter()
    judge = judge_model(model)
    for i, item in enumerate(golden_dataset, 1):
        case = dataset[item["case_idx"]]
        verdict = judge.invoke(
            build_judge_prompt(case["input"], item["output"], case["criteria"])
        )
        predicted, reasoning = parse_judge_verdict(verdict)
        gold = item["gold_label"]
        if predicted == "pass" and gold == "pass":
            tp += 1; outcome = "TP"
        elif predicted == "pass" and gold == "fail":
            fp += 1; outcome = "FP"
        elif predicted == "fail" and gold == "fail":
            tn += 1; outcome = "TN"
        else:
            fn += 1; outcome = "FN"
        print(f"[{i:2d}] case {item['case_idx'] + 1} gold={gold} pred={predicted} → {outcome}")
        rows.append((i, item["case_idx"] + 1, gold, predicted, outcome, reasoning))
    elapsed = time.perf_counter() - start

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(golden_dataset)

    print(f"\nTP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Precision={precision:.2%}  Recall={recall:.2%}  F1={f1:.2%}  "
          f"Accuracy={accuracy:.2%}  ({elapsed:.1f}s)")

    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Judge Precision/Recall — {timestamp}",
        "",
        f"- **Examples:** {len(golden_dataset)}  ",
        f"- **TP/FP/TN/FN:** {tp}/{fp}/{tn}/{fn}  ",
        f"- **Precision:** {precision:.2%}  ",
        f"- **Recall:** {recall:.2%}  ",
        f"- **F1:** {f1:.2%}  ",
        f"- **Accuracy:** {accuracy:.2%}  ",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "| # | Case | Gold | Predicted | Outcome | Judge reasoning |",
        "|---|------|------|-----------|---------|-----------------|",
        *[f"| {n} | {c} | {g} | {p} | {o} | {r.replace('|', '\\|')} |"
          for n, c, g, p, o, r in rows],
    ]
    out_path = Path(__file__).parent / f"judge-pr-{timestamp.replace(':', '-')}.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"\nReport saved to {out_path.name}")


async def judge_stability_check(trials: int = 5) -> None:
    data = dataset[6]
    if not CASE7_FIXTURE.exists():
        print(f"No fixture at {CASE7_FIXTURE}. Run a full eval first to capture one.")
        return
    output = CASE7_FIXTURE.read_text()
    verdicts, reasonings = [], []
    start = time.perf_counter()
    judge_llm = judge_model()
    for t in range(trials):
        verdict = judge_llm.invoke(
            build_judge_prompt(data["input"], output, data["criteria"])
        )
        judge, reasoning = parse_judge_verdict(verdict)
        verdicts.append(judge); reasonings.append(reasoning)
        print(f"[judge {t + 1}] {judge} — {reasoning}")
    elapsed = time.perf_counter() - start
    pass_n, fail_n = verdicts.count("pass"), verdicts.count("fail")
    agreement = max(pass_n, fail_n) / trials
    diagnosis = (
        "STABLE — judge is consistent; flips during eval reflect agent output drift"
        if agreement == 1.0
        else "UNSTABLE — judge itself is noisy; flips aren't just agent drift"
    )
    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Judge Stability Check — {timestamp}",
        "",
        "## Summary",
        "",
        f"- **Case:** 7 — {data['input']}",
        f"- **Trials:** {trials} (judge calls only, fixed agent output)",
        f"- **Verdicts:** pass={pass_n}, fail={fail_n}",
        f"- **Agreement:** {agreement:.0%}",
        f"- **Diagnosis:** {diagnosis}",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Judge criteria",
        "",
        *[f"{j + 1}. {c}" for j, c in enumerate(data["criteria"])],
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
    out_path = Path(__file__).parent / f"judge-check-{timestamp.replace(':', '-')}.md"
    out_path.write_text(summary + "\n")
    print(f"\nReport saved to {out_path.name}")


async def main() -> None:
    agent = await build_agent()
    judge = judge_model()
    results = []
    start = time.perf_counter()
    for idx, data in enumerate(dataset):
        print(f"\n--- {data['tags']} ---")
        print(f"Q: {data['input']}")
        rule_pass = judge_pass = rule_applicable = 0
        outputs, reasonings = [], []
        for t in range(TRIALS):
            final_output = await run_agent(agent, data["input"])
            print(f"[trial {t + 1}] {final_output}")
            outputs.append(final_output)
            if data.get("expected"):
                rule_applicable += 1
                if data["expected"] in final_output:
                    rule_pass += 1
            verdict = judge.invoke(
                build_judge_prompt(data["input"], final_output, data["criteria"])
            )
            judge_label, judge_reasoning = parse_judge_verdict(verdict)
            print(f"[trial {t + 1}] judge: {judge_label} — {judge_reasoning}")
            reasonings.append(f"T{t + 1}: {judge_reasoning}")
            if judge_label == "pass":
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
    print_summary(results, time.perf_counter() - start)



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "judge-check":
        asyncio.run(judge_stability_check())
    elif len(sys.argv) > 1 and sys.argv[1] == "judge-pr":
        run_judge_pr()
    else:
        asyncio.run(main())

