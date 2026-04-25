"""Compare two eval runs by per-criterion pass-rate deltas.

Groups verdicts by (case, criterion), computes Wilson score CIs, and emits a
markdown report. Loud banner when run_a.config_hash != run_b.config_hash —
you are comparing apples and oranges, so the deltas aren't causal.
"""
import math

import db
from report import md_escape, write_report

Z_95 = 1.959964  # 95% Wilson CI


def wilson_ci(pass_n: int, total: int) -> tuple[float, float, float]:
    """Return (point, low, high) for 95% Wilson score interval."""
    if total == 0:
        return 0.0, 0.0, 0.0
    p = pass_n / total
    z = Z_95
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = (z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def _agg(conn, run_id: int) -> dict[tuple[int | None, int, str], dict]:
    """Group verdicts by (case_id, criterion_idx, judge_name). Returns pass_n/total per group."""
    rows = conn.execute(
        """
        SELECT cr.case_id, cr.idx, cr.text, v.judge_name,
               SUM(CASE WHEN v.score = 1 THEN 1 ELSE 0 END) AS pass_n,
               COUNT(v.verdict_id) AS total
        FROM criterion_verdicts v
        JOIN criteria cr ON cr.criterion_id = v.criterion_id
        WHERE v.run_id = ?
        GROUP BY cr.case_id, cr.idx, v.judge_name
        """,
        (run_id,),
    ).fetchall()
    out: dict[tuple[int | None, int, str], dict] = {}
    for r in rows:
        out[(r["case_id"], r["idx"], r["judge_name"])] = {
            "text": r["text"],
            "pass_n": r["pass_n"],
            "total": r["total"],
        }
    return out


def render_compare(run_a: int, run_b: int) -> str:
    conn = db.connect()
    try:
        a_row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_a,)).fetchone()
        b_row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_b,)).fetchone()
        if a_row is None or b_row is None:
            raise LookupError(f"run not found: {run_a if a_row is None else run_b}")

        a = _agg(conn, run_a)
        b = _agg(conn, run_b)
        # Sort with None case_id (global criteria like faithfulness) last.
        keys = sorted(set(a) | set(b), key=lambda k: (k[0] is None, k[0] or 0, k[2], k[1]))

        cases_by_id = {
            r["case_id"]: r["input"]
            for r in conn.execute("SELECT case_id, input FROM cases").fetchall()
        }

        lines = [f"# Compare -- run {run_a} vs run {run_b}", ""]
        if a_row["config_hash"] != b_row["config_hash"]:
            lines += [
                "> **WARNING: config_hash differs between runs.** Differences below",
                "> may reflect config drift (model, prompt version, trials, temperature),",
                "> not agent behavior change.",
                "",
                f"- run {run_a} config_hash: `{a_row['config_hash'][:12]}`",
                f"- run {run_b} config_hash: `{b_row['config_hash'][:12]}`",
                "",
            ]

        lines += [
            f"- **Run A ({run_a}):** {a_row['started_at']} -- {a_row['agent_model']}",
            f"- **Run B ({run_b}):** {b_row['started_at']} -- {b_row['agent_model']}",
            "",
            "## Per-criterion deltas",
            "",
            "| Case | Judge | # | Criterion | A pass | B pass | Δ (B-A) | A 95% CI | B 95% CI |",
            "|------|-------|---|-----------|--------|--------|---------|----------|----------|",
        ]

        for (case_id, idx, judge) in keys:
            a_s = a.get((case_id, idx, judge), {"pass_n": 0, "total": 0, "text": ""})
            b_s = b.get((case_id, idx, judge), {"pass_n": 0, "total": 0, "text": ""})
            text = a_s["text"] or b_s["text"]
            case_label = (
                "(global)" if case_id is None
                else f"C{case_id}: " + md_escape(cases_by_id.get(case_id, "?"))[:40]
            )
            a_p, a_lo, a_hi = wilson_ci(a_s["pass_n"], a_s["total"])
            b_p, b_lo, b_hi = wilson_ci(b_s["pass_n"], b_s["total"])
            delta = b_p - a_p
            arrow = "↑" if delta > 0.0001 else ("↓" if delta < -0.0001 else "·")
            lines.append(
                f"| {case_label} | {judge} | {idx} | {md_escape(text)[:60]} "
                f"| {a_s['pass_n']}/{a_s['total']} ({a_p:.0%}) "
                f"| {b_s['pass_n']}/{b_s['total']} ({b_p:.0%}) "
                f"| {arrow} {delta:+.0%} "
                f"| [{a_lo:.0%},{a_hi:.0%}] "
                f"| [{b_lo:.0%},{b_hi:.0%}] |"
            )

        # Rollups per judge.
        lines += ["", "## Rollup by judge", "", "| Judge | A | B | Δ |", "|-------|---|---|---|"]
        for judge in ("correctness", "faithfulness"):
            a_p_n = sum(v["pass_n"] for k, v in a.items() if k[2] == judge)
            a_tot = sum(v["total"] for k, v in a.items() if k[2] == judge)
            b_p_n = sum(v["pass_n"] for k, v in b.items() if k[2] == judge)
            b_tot = sum(v["total"] for k, v in b.items() if k[2] == judge)
            a_rate = a_p_n / a_tot if a_tot else 0
            b_rate = b_p_n / b_tot if b_tot else 0
            lines.append(
                f"| {judge} | {a_p_n}/{a_tot} ({a_rate:.0%}) "
                f"| {b_p_n}/{b_tot} ({b_rate:.0%}) | {b_rate - a_rate:+.0%} |"
            )
        return "\n".join(lines) + "\n"
    finally:
        conn.close()


def render_and_save(run_a: int, run_b: int) -> str:
    body = render_compare(run_a, run_b)
    path = write_report(f"compare-{run_a}-vs-{run_b}", body)
    return path.name
