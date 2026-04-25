"""Render a markdown eval report from SQLite for a given run_id.

Output matches the pre-slice format produced by run_eval._summarize so the
diff against archived reports is trivial.
"""
import json
import sqlite3

import db
from report import md_escape, write_report


def _pct(p: int, t: int) -> str:
    return f"{p}/{t} ({(p / t if t else 0):.0%})"


def _avg(total: int, n: int) -> float:
    return total / n if n else 0.0


def _percentile(xs: list[int], p: float) -> int | None:
    if not xs:
        return None
    s = sorted(xs)
    idx = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[idx]


def _run_cost_rollup(conn: sqlite3.Connection, run_id: int) -> dict:
    """Sum agent vs judge costs/tokens, latency p50/p95."""
    agent = conn.execute(
        """
        SELECT COALESCE(SUM(cost_usd), 0)   AS cost,
               COALESCE(SUM(tokens_in), 0)  AS tin,
               COALESCE(SUM(tokens_out), 0) AS tout,
               COUNT(latency_ms)            AS n_lat
        FROM trials WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    agent_latencies = [
        r["latency_ms"] for r in conn.execute(
            "SELECT latency_ms FROM trials WHERE run_id = ? AND latency_ms IS NOT NULL",
            (run_id,),
        ).fetchall()
    ]
    judge_rows = conn.execute(
        """
        SELECT judge_name,
               COALESCE(SUM(judge_cost_usd), 0)   AS cost,
               COALESCE(SUM(judge_tokens_in), 0)  AS tin,
               COALESCE(SUM(judge_tokens_out), 0) AS tout
        FROM criterion_verdicts
        WHERE run_id = ? AND judge_cost_usd IS NOT NULL
        GROUP BY judge_name
        """,
        (run_id,),
    ).fetchall()
    judge_lat = {
        r["judge_name"]: [
            row["judge_latency_ms"] for row in conn.execute(
                """
                SELECT judge_latency_ms FROM criterion_verdicts
                WHERE run_id = ? AND judge_name = ? AND judge_latency_ms IS NOT NULL
                """,
                (run_id, r["judge_name"]),
            ).fetchall()
        ]
        for r in judge_rows
    }
    return {
        "agent_cost": agent["cost"],
        "agent_tokens_in": agent["tin"],
        "agent_tokens_out": agent["tout"],
        "agent_p50": _percentile(agent_latencies, 0.5),
        "agent_p95": _percentile(agent_latencies, 0.95),
        "judges": {
            r["judge_name"]: {
                "cost": r["cost"],
                "tokens_in": r["tin"],
                "tokens_out": r["tout"],
                "p50": _percentile(judge_lat[r["judge_name"]], 0.5),
                "p95": _percentile(judge_lat[r["judge_name"]], 0.95),
            }
            for r in judge_rows
        },
    }


def _case_rows(conn: sqlite3.Connection, run_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.case_id, c.input, c.tags, c.expected
        FROM cases c
        WHERE c.case_id IN (SELECT DISTINCT case_id FROM trials WHERE run_id = ?)
        ORDER BY c.case_id
        """,
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _case_stats(conn: sqlite3.Connection, run_id: int, case_id: int) -> dict:
    trials = conn.execute(
        "SELECT trial_id, trial_idx, output FROM trials WHERE run_id = ? AND case_id = ? ORDER BY trial_idx",
        (run_id, case_id),
    ).fetchall()

    # Correctness per-criterion rollup.
    crit_rows = conn.execute(
        """
        SELECT cr.criterion_id, cr.idx, cr.text,
               COALESCE(SUM(v.score), 0) AS pass_n,
               COUNT(v.verdict_id)        AS total,
               COALESCE(SUM(v.confidence), 0) AS conf_sum
        FROM criteria cr
        LEFT JOIN criterion_verdicts v
          ON v.criterion_id = cr.criterion_id
         AND v.run_id = ?
         AND v.judge_name = 'correctness'
        WHERE cr.case_id = ? AND cr.judge_name = 'correctness'
        GROUP BY cr.criterion_id
        ORDER BY cr.idx
        """,
        (run_id, case_id),
    ).fetchall()
    correctness_stats = [
        {
            "criterion": r["text"],
            "pass_n": r["pass_n"],
            "total": r["total"],
            "conf_sum": r["conf_sum"],
        }
        for r in crit_rows
    ]

    # Per-trial correctness label = pass iff every correctness verdict for that trial passes.
    per_trial_correct = conn.execute(
        """
        SELECT trial_id,
               COUNT(*) AS n,
               SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) AS pass_n,
               SUM(CASE WHEN score IS NULL THEN 1 ELSE 0 END) AS unknown_n,
               AVG(confidence) AS avg_conf,
               MIN(confidence) AS min_conf
        FROM criterion_verdicts
        WHERE run_id = ? AND judge_name = 'correctness'
          AND trial_id IN (SELECT trial_id FROM trials WHERE run_id = ? AND case_id = ?)
        GROUP BY trial_id
        """,
        (run_id, run_id, case_id),
    ).fetchall()
    correctness_case_pass = sum(
        1 for t in per_trial_correct
        if t["unknown_n"] == 0 and t["pass_n"] == t["n"]
    )
    correctness_case_conf_avg = _avg(sum(t["min_conf"] or 0 for t in per_trial_correct), len(per_trial_correct))

    # Faithfulness (single criterion).
    per_trial_faith = conn.execute(
        """
        SELECT trial_id, score, confidence, reasoning
        FROM criterion_verdicts
        WHERE run_id = ? AND judge_name = 'faithfulness'
          AND trial_id IN (SELECT trial_id FROM trials WHERE run_id = ? AND case_id = ?)
        """,
        (run_id, run_id, case_id),
    ).fetchall()
    faith_case_pass = sum(1 for t in per_trial_faith if t["score"] == 1)
    faith_case_conf_avg = _avg(sum(t["confidence"] for t in per_trial_faith), len(per_trial_faith))

    # Rule-based (expected substring in any trial output).
    expected = conn.execute("SELECT expected FROM cases WHERE case_id = ?", (case_id,)).fetchone()["expected"]
    rule_total = len(trials) if expected else 0
    rule_pass = sum(1 for t in trials if expected and expected in t["output"])

    # Last-trial evidence count.
    last_trial_id = trials[-1]["trial_id"] if trials else None
    evidence_len = 0
    if last_trial_id is not None:
        evidence_len = conn.execute(
            "SELECT COUNT(*) AS n FROM tool_calls WHERE trial_id = ?", (last_trial_id,)
        ).fetchone()["n"]

    # Reasoning strings (T1 … T3) per judge.
    c_reasonings = _per_trial_reasonings(conn, run_id, case_id, "correctness")
    f_reasonings = _per_trial_reasonings(conn, run_id, case_id, "faithfulness")

    return {
        "trials": len(trials),
        "output": trials[-1]["output"] if trials else "",
        "rule_pass": rule_pass,
        "rule_total": rule_total,
        "correctness_case_pass": correctness_case_pass,
        "correctness_case_conf_avg": correctness_case_conf_avg,
        "correctness_criteria_stats": correctness_stats,
        "faithfulness_case_pass": faith_case_pass,
        "faithfulness_case_conf_avg": faith_case_conf_avg,
        "correctness_reasoning": " || ".join(c_reasonings),
        "faithfulness_reasoning": " || ".join(f_reasonings),
        "evidence_len": evidence_len,
    }


def _per_trial_reasonings(conn: sqlite3.Connection, run_id: int, case_id: int, judge_name: str) -> list[str]:
    trials = conn.execute(
        "SELECT trial_id, trial_idx FROM trials WHERE run_id = ? AND case_id = ? ORDER BY trial_idx",
        (run_id, case_id),
    ).fetchall()
    out: list[str] = []
    for tr in trials:
        verdicts = conn.execute(
            """
            SELECT cr.idx, v.score, v.confidence, v.reasoning
            FROM criterion_verdicts v
            JOIN criteria cr ON cr.criterion_id = v.criterion_id
            WHERE v.trial_id = ? AND v.judge_name = ?
            ORDER BY cr.idx
            """,
            (tr["trial_id"], judge_name),
        ).fetchall()
        if not verdicts:
            continue
        label_of = lambda s: "pass" if s == 1 else ("fail" if s == 0 else "unknown")
        trial_label = (
            "unknown" if any(v["score"] is None for v in verdicts)
            else ("pass" if all(v["score"] == 1 for v in verdicts) else "fail")
        )
        trial_conf = min(v["confidence"] for v in verdicts)
        parts = " | ".join(f"[{v['idx']}] {label_of(v['score'])}: {v['reasoning']}" for v in verdicts)
        out.append(f"T{tr['trial_idx']} ({trial_label}, conf {trial_conf}): {parts}")
    return out


def render(run_id: int, *, conn: sqlite3.Connection | None = None) -> str:
    owns = conn is None
    conn = conn or db.connect()
    try:
        run = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if run is None:
            raise LookupError(f"run_id {run_id} not found")
        trials_per_case = run["trials_per_case"]

        cases = _case_rows(conn, run_id)
        results = []
        for case in cases:
            stats = _case_stats(conn, run_id, case["case_id"])
            results.append({
                "input": case["input"],
                "tags": json.loads(case["tags"] or "[]"),
                **stats,
            })

        rule_pass = sum(r["rule_pass"] for r in results)
        rule_total = sum(r["rule_total"] for r in results)
        case_total = sum(r["trials"] for r in results)
        case_pass = sum(r["correctness_case_pass"] for r in results)
        faith_case_pass = sum(r["faithfulness_case_pass"] for r in results)
        c_crit_p = sum(sum(c["pass_n"] for c in r["correctness_criteria_stats"]) for r in results)
        c_crit_t = sum(sum(c["total"] for c in r["correctness_criteria_stats"]) for r in results)
        c_crit_conf = sum(sum(c["conf_sum"] for c in r["correctness_criteria_stats"]) for r in results)
        c_case_conf = _avg(sum(r["correctness_case_conf_avg"] for r in results), len(results))
        f_case_conf = _avg(sum(r["faithfulness_case_conf_avg"] for r in results), len(results))

        started = run["started_at"]
        ended = run["ended_at"]
        elapsed_line = f"- **Run window:** {started} → {ended or 'in-progress'}"

        cost = _run_cost_rollup(conn, run_id)
        judge_costs = cost["judges"]
        judge_total = sum(j["cost"] for j in judge_costs.values())
        total_cost = cost["agent_cost"] + judge_total

        cost_lines = [
            "## Cost & latency",
            "",
            f"- **Total cost:** ${total_cost:.4f} "
            f"(agent ${cost['agent_cost']:.4f} / judges ${judge_total:.4f})",
            f"- **Agent tokens:** in {cost['agent_tokens_in']}, out {cost['agent_tokens_out']}",
            f"- **Agent latency p50/p95:** "
            f"{cost['agent_p50'] or 0}ms / {cost['agent_p95'] or 0}ms",
        ]
        for name, j in judge_costs.items():
            cost_lines.append(
                f"- **Judge `{name}`:** ${j['cost']:.4f}, "
                f"in {j['tokens_in']}, out {j['tokens_out']}, "
                f"p50/p95 {j['p50'] or 0}ms / {j['p95'] or 0}ms"
            )
        cost_lines.append("")

        lines = [
            f"# Eval Report -- run {run_id}",
            "",
            "## Summary",
            "",
            f"- **Trials per case:** {trials_per_case}",
            f"- **Cases:** {len(results)}",
            f"- **Rule-based pass rate:** {_pct(rule_pass, rule_total)}",
            f"- **Correctness case pass rate (all criteria pass):** {_pct(case_pass, case_total)} (avg conf {c_case_conf:.1f})",
            f"- **Correctness per-criterion pass rate:** {_pct(c_crit_p, c_crit_t)} (avg conf {_avg(c_crit_conf, c_crit_t):.1f})",
            f"- **Faithfulness pass rate:** {_pct(faith_case_pass, case_total)} (avg conf {f_case_conf:.1f})",
            elapsed_line,
            f"- **Config hash:** `{run['config_hash'][:12]}`",
            "",
            *cost_lines,
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
                    f"| {j + 1} | {md_escape(c['criterion'])} | {c['pass_n']}/{c['total']} "
                    f"| {_avg(c['conf_sum'], c['total']):.1f} |"
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
    finally:
        if owns:
            conn.close()


def render_and_save(run_id: int) -> str:
    body = render(run_id)
    path = write_report("results", body)
    return path.name
