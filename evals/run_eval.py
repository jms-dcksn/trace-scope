"""Core eval: run the agent N times per case, score with rule + judges, report."""
import time

import db
from agent import SYSTEM_PROMPT, SearchAgent
from data import dataset, reference_output
from judge import FAITHFULNESS_CRITERION, CorrectnessJudge, FaithfulnessJudge, ToolUseJudge, render_trace
from report import md_escape, timestamp, write_report

TRIALS = 3


def _crit_totals(results, key):
    p = sum(sum(c["pass_n"] for c in r[key]) for r in results)
    t = sum(sum(c["total"] for c in r[key]) for r in results)
    conf = sum(sum(c["conf_sum"] for c in r[key]) for r in results)
    return p, t, conf


def _avg_conf(stat):
    return stat["conf_sum"] / stat["total"] if stat["total"] else 0


def _summarize(results, elapsed):
    rule_pass = sum(r["rule_pass"] for r in results)
    rule_total = sum(r["rule_total"] for r in results)
    case_pass = sum(r["correctness_case_pass"] for r in results)
    faith_case_pass = sum(r["faithfulness_case_pass"] for r in results)
    case_total = sum(r["trials"] for r in results)
    c_crit_p, c_crit_t, c_crit_conf = _crit_totals(results, "correctness_criteria_stats")
    c_case_conf = sum(r["correctness_case_conf_avg"] for r in results) / len(results) if results else 0
    f_case_conf = sum(r["faithfulness_case_conf_avg"] for r in results) / len(results) if results else 0

    def pct(p, t):
        return f"{p}/{t} ({(p / t if t else 0):.0%})"

    def conf(total_conf, total_n):
        return f"{(total_conf / total_n if total_n else 0):.1f}"

    ts = timestamp()
    lines = [
        f"# Eval Report -- {ts}",
        "",
        "## Summary",
        "",
        f"- **Trials per case:** {TRIALS}",
        f"- **Cases:** {len(results)}",
        f"- **Rule-based pass rate:** {pct(rule_pass, rule_total)}",
        f"- **Correctness case pass rate (all criteria pass):** {pct(case_pass, case_total)} (avg conf {c_case_conf:.1f})",
        f"- **Correctness per-criterion pass rate:** {pct(c_crit_p, c_crit_t)} (avg conf {conf(c_crit_conf, c_crit_t)})",
        f"- **Faithfulness pass rate:** {pct(faith_case_pass, case_total)} (avg conf {f_case_conf:.1f})",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "## Per-case results",
        "",
        "| # | Difficulty | Rule | Correct (conf) | Faithful (conf) | Evidence | Input |",
        "|---|------------|------|----------------|-----------------|----------|-------|",
    ]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        rule = f"{r['rule_pass']}/{r['rule_total']}" if r["rule_total"] else "n/a"
        lines.append(
            f"| {i} | {difficulty} | {rule} "
            f"| {r['correctness_case_pass']}/{r['trials']} ({r['correctness_case_conf_avg']:.0f}) "
            f"| {r['faithfulness_case_pass']}/{r['trials']} ({r['faithfulness_case_conf_avg']:.0f}) "
            f"| {r['evidence_len']} "
            f"| {md_escape(r['input'])[:100]} |"
        )

    lines += ["", "## Case details", ""]
    for i, r in enumerate(results, 1):
        difficulty = next((t for t in r["tags"] if t in ("simple", "medium", "hard")), "?")
        lines += [
            f"### Case {i} -- {difficulty}",
            "",
            f"**Input:** {r['input']}",
            "",
            "**Last trial output:**",
            "",
            "```",
            r["output"],
            "```",
            "",
            f"**Correctness:** case pass {r['correctness_case_pass']}/{r['trials']} "
            f"(avg conf {r['correctness_case_conf_avg']:.1f})",
            "",
            "| # | Criterion | Pass rate | Avg conf |",
            "|---|-----------|-----------|----------|",
            *[
                f"| {j + 1} | {md_escape(c['criterion'])} | {c['pass_n']}/{c['total']} | {_avg_conf(c):.1f} |"
                for j, c in enumerate(r["correctness_criteria_stats"])
            ],
            "",
            f"**Faithfulness:** {r['faithfulness_case_pass']}/{r['trials']} "
            f"(avg conf {r['faithfulness_case_conf_avg']:.1f}, "
            f"evidence: {r['evidence_len']} searches on last trial)",
            "",
            f"**Correctness reasoning:** {r['correctness_reasoning']}",
            "",
            f"**Faithfulness reasoning:** {r['faithfulness_reasoning']}",
            "",
        ]
    return "\n".join(lines)


async def run_dataset_eval(indices=None):
    agent = SearchAgent()
    await agent.setup()
    correctness = CorrectnessJudge()
    faithfulness = FaithfulnessJudge()
    tool_use = ToolUseJudge()
    results = []
    start = time.perf_counter()

    conn = db.connect()
    db.seed_cases_from_dataset(conn, dataset, FAITHFULNESS_CRITERION)
    db.seed_case_expectations(conn, dataset)
    run_id = db.insert_run(
        conn,
        agent_model=agent.model,
        agent_system_prompt=SYSTEM_PROMPT,
        trials_per_case=TRIALS,
        judge_models={
            correctness.name: correctness.model,
            faithfulness.name: faithfulness.model,
            tool_use.name: tool_use.model,
        },
        judge_prompt_versions={
            correctness.name: correctness.PROMPT_VERSION,
            faithfulness.name: faithfulness.PROMPT_VERSION,
            tool_use.name: tool_use.PROMPT_VERSION,
        },
        judge_temperatures={correctness.name: 0.0, faithfulness.name: 0.0, tool_use.name: 0.0},
    )
    print(f"SQLite run_id={run_id}")
    faith_crit_id = db.get_faithfulness_criterion_id(conn)

    cases = (
        [(i, dataset[i]) for i in indices] if indices is not None
        else list(enumerate(dataset))
    )
    for idx, data in cases:
        print(f"\n--- {data['tags']} ---")
        print(f"Q: {data['input']}")
        case_id = db.get_case_id(conn, data["input"])
        correctness_crit_ids = db.get_correctness_criterion_ids(conn, case_id)
        tool_use_payload = db.get_tool_use_expectations(conn, case_id)
        tool_use_crit_ids = db.get_tool_use_criterion_ids(conn, case_id) if tool_use_payload else []
        rule_pass = rule_total = 0
        correctness_case_pass = faithfulness_case_pass = 0
        c_case_conf_sum = f_case_conf_sum = 0
        outputs, c_reasonings, f_reasonings = [], [], []
        last_evidence_len = 0
        correctness_stats = [
            {"criterion": c, "pass_n": 0, "total": 0, "conf_sum": 0}
            for c in data["criteria"]
        ]
        faithfulness_stats = [
            {"criterion": c, "pass_n": 0, "total": 0, "conf_sum": 0}
            for c in faithfulness.criteria
        ]
        ref = reference_output(idx)

        for t in range(TRIALS):
            try:
                run = await agent.ask(data["input"])
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                print(f"[trial {t + 1}] AGENT ERROR: {err}")
                db.insert_trial(
                    conn, run_id=run_id, case_id=case_id,
                    trial_idx=t + 1, output="", error=err,
                )
                conn.commit()
                continue
            print(f"[trial {t + 1}] {run.output}")
            print(f"[trial {t + 1}] evidence: {len(run.evidence)} search(es)")
            outputs.append(run.output)
            last_evidence_len = len(run.evidence)

            trace_id = db.insert_trace(conn, content=render_trace(run.evidence))
            trial_id = db.insert_trial(
                conn, run_id=run_id, case_id=case_id,
                trial_idx=t + 1, output=run.output,
                trace_id=trace_id,
                latency_ms=run.latency_ms,
                tokens_in=run.tokens_in,
                tokens_out=run.tokens_out,
                cost_usd=run.cost_usd,
            )
            for call_idx, call in enumerate(run.evidence, 1):
                db.insert_tool_call(
                    conn, trial_id=trial_id, idx=call_idx,
                    tool_name="web_search",
                    args={"query": call.query},
                    result=call.results,
                    latency_ms=call.latency_ms,
                )

            if data.get("expected"):
                rule_total += 1
                if data["expected"] in run.output:
                    rule_pass += 1

            c_res = correctness.evaluate(data["input"], run.output, data["criteria"], ref)
            print(f"[trial {t + 1}] correctness: {c_res.label} (conf {c_res.confidence})")
            for j, cr in enumerate(c_res.per_criterion):
                correctness_stats[j]["total"] += 1
                correctness_stats[j]["conf_sum"] += cr.confidence
                if cr.label == "pass":
                    correctness_stats[j]["pass_n"] += 1
                print(f"    C[{j + 1}] {cr.label} (conf {cr.confidence}) -- {cr.reasoning}")
                # Judge metrics belong to the call (1 per trial), not per criterion.
                # Attach to first row only so SUM() gives real call totals.
                first = j == 0
                db.insert_criterion_verdict(
                    conn, run_id=run_id, trial_id=trial_id,
                    criterion_id=correctness_crit_ids[j],
                    judge_name=correctness.name, judge_model=correctness.model,
                    label=cr.label, confidence=cr.confidence, reasoning=cr.reasoning,
                    judge_latency_ms=c_res.latency_ms if first else None,
                    judge_tokens_in=c_res.tokens_in if first else None,
                    judge_tokens_out=c_res.tokens_out if first else None,
                    judge_cost_usd=c_res.cost_usd if first else None,
                )
            c_reasonings.append(
                f"T{t + 1} ({c_res.label}, conf {c_res.confidence}): {c_res.reasoning}"
            )
            c_case_conf_sum += c_res.confidence
            if c_res.label == "pass":
                correctness_case_pass += 1

            f_res = faithfulness.evaluate(data["input"], run.output, run.evidence)
            print(f"[trial {t + 1}] faithfulness: {f_res.label} (conf {f_res.confidence})")
            for j, cr in enumerate(f_res.per_criterion):
                faithfulness_stats[j]["total"] += 1
                faithfulness_stats[j]["conf_sum"] += cr.confidence
                if cr.label == "pass":
                    faithfulness_stats[j]["pass_n"] += 1
                print(f"    F[{j + 1}] {cr.label} (conf {cr.confidence}) -- {cr.reasoning}")
                first = j == 0
                db.insert_criterion_verdict(
                    conn, run_id=run_id, trial_id=trial_id,
                    criterion_id=faith_crit_id,
                    judge_name=faithfulness.name, judge_model=faithfulness.model,
                    label=cr.label, confidence=cr.confidence, reasoning=cr.reasoning,
                    judge_latency_ms=f_res.latency_ms if first else None,
                    judge_tokens_in=f_res.tokens_in if first else None,
                    judge_tokens_out=f_res.tokens_out if first else None,
                    judge_cost_usd=f_res.cost_usd if first else None,
                )
            f_reasonings.append(
                f"T{t + 1} ({f_res.label}, conf {f_res.confidence}): {f_res.reasoning}"
            )
            f_case_conf_sum += f_res.confidence
            if f_res.label == "pass":
                faithfulness_case_pass += 1

            if tool_use_payload:
                queries = [c.query for c in run.evidence]
                tu_res = tool_use.evaluate(queries, tool_use_payload)
                print(f"[trial {t + 1}] tool_use: {tu_res.label}")
                for j, cr in enumerate(tu_res.per_criterion):
                    print(f"    T[{j + 1}] {cr.label} -- {cr.reasoning}")
                    first = j == 0
                    db.insert_criterion_verdict(
                        conn, run_id=run_id, trial_id=trial_id,
                        criterion_id=tool_use_crit_ids[j],
                        judge_name=tool_use.name, judge_model=tool_use.model,
                        label=cr.label, confidence=cr.confidence, reasoning=cr.reasoning,
                        judge_latency_ms=tu_res.latency_ms if first else None,
                        judge_tokens_in=tu_res.tokens_in if first else None,
                        judge_tokens_out=tu_res.tokens_out if first else None,
                        judge_cost_usd=tu_res.cost_usd if first else None,
                    )

        conn.commit()  # commit per case for crash safety

        results.append({
            "input": data["input"],
            "output": outputs[-1],
            "tags": data["tags"],
            "criteria": data["criteria"],
            "rule_pass": rule_pass,
            "rule_total": rule_total,
            "trials": TRIALS,
            "correctness_case_pass": correctness_case_pass,
            "faithfulness_case_pass": faithfulness_case_pass,
            "correctness_case_conf_avg": c_case_conf_sum / TRIALS,
            "faithfulness_case_conf_avg": f_case_conf_sum / TRIALS,
            "correctness_criteria_stats": correctness_stats,
            "faithfulness_criteria_stats": faithfulness_stats,
            "correctness_reasoning": " || ".join(c_reasonings),
            "faithfulness_reasoning": " || ".join(f_reasonings),
            "evidence_len": last_evidence_len,
        })

    db.finalize_run(conn, run_id)
    conn.close()
    summary = _summarize(results, time.perf_counter() - start)
    print("\n\n" + summary)
    path = write_report("results", summary)
    print(f"\nReport saved to {path.name}")
