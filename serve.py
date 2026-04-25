"""Lightweight read-only viewer for evals.db. Stdlib only.

Run:
    uv run python serve.py            # http://localhost:8000
    uv run python serve.py 8080       # custom port
"""
import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import db

REPORTS_DIR = Path(__file__).parent / "results"


# ---------- shared HTML ----------

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
       max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
h1, h2, h3 { font-weight: 600; }
h1 { font-size: 1.4rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.1rem; margin-top: 2rem; border-bottom: 1px solid #8884; padding-bottom: 0.3rem; }
h3 { font-size: 1rem; margin-top: 1.2rem; }
nav { padding: 0.6rem 0; border-bottom: 1px solid #8884; margin-bottom: 1.5rem; }
nav a { margin-right: 1rem; }
table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }
th, td { text-align: left; padding: 0.35rem 0.6rem; border-bottom: 1px solid #8882; vertical-align: top; }
th { font-weight: 600; background: #8881; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
code, pre { font-family: 'SF Mono', Menlo, monospace; font-size: 12.5px; }
pre { background: #8881; padding: 0.6rem 0.8rem; border-radius: 4px;
      overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
.pass { color: #1a7f37; font-weight: 600; }
.fail { color: #cf222e; font-weight: 600; }
.muted { color: #888; }
.tag  { display: inline-block; padding: 1px 6px; border-radius: 3px;
        background: #8882; font-size: 11px; }
.diff { background: #ffeac4; }
.disagree { background: #ffe1e1; }
small { color: #888; }
.kvs { display: grid; grid-template-columns: max-content 1fr; gap: 0.2rem 1rem; }
.kvs dt { font-weight: 600; }
.kvs dd { margin: 0; font-variant-numeric: tabular-nums; }
"""


def page(title: str, body: str) -> bytes:
    nav = (
        '<nav><a href="/">overview</a> <a href="/runs">runs</a> '
        '<a href="/cases">cases</a> <a href="/gold">gold</a></nav>'
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)} — evals</title>
<style>{CSS}</style></head><body>
{nav}<h1>{html.escape(title)}</h1>{body}
</body></html>""".encode()


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def fmt_pass(score) -> str:
    if score == 1: return '<span class="pass">pass</span>'
    if score == 0: return '<span class="fail">fail</span>'
    return '<span class="muted">unknown</span>'


def trunc(s, n=120):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[:n] + "…"


# ---------- pages ----------

def page_index(conn) -> bytes:
    rows = conn.execute("""
        SELECT
          (SELECT COUNT(*) FROM cases) AS cases,
          (SELECT COUNT(*) FROM runs) AS runs,
          (SELECT COUNT(*) FROM trials) AS trials,
          (SELECT COUNT(*) FROM criterion_verdicts) AS verdicts,
          (SELECT COUNT(*) FROM fixed_outputs) AS fixed_outputs,
          (SELECT COUNT(*) FROM gold_labels) AS gold_labels,
          (SELECT COUNT(*) FROM tool_calls) AS tool_calls,
          (SELECT COUNT(*) FROM traces) AS traces
    """).fetchone()
    body = (
        '<dl class="kvs">'
        + "".join(f"<dt>{k}</dt><dd>{rows[k]}</dd>" for k in rows.keys())
        + "</dl>"
        '<p class="muted">read-only view of evals.db. start with '
        '<a href="/runs">runs</a> or <a href="/gold">gold</a>.</p>'
    )
    return page("overview", body)


def page_runs(conn) -> bytes:
    rows = conn.execute("""
        SELECT r.run_id, r.started_at, r.ended_at, r.agent_model, r.tag,
               COUNT(DISTINCT t.case_id) AS cases,
               COUNT(t.trial_id) AS trials,
               SUBSTR(r.config_hash, 1, 12) AS cfg,
               COALESCE((SELECT SUM(cost_usd) FROM trials WHERE run_id=r.run_id), 0) AS agent_cost,
               COALESCE((SELECT SUM(judge_cost_usd) FROM criterion_verdicts WHERE run_id=r.run_id), 0) AS judge_cost
        FROM runs r LEFT JOIN trials t ON t.run_id = r.run_id
        GROUP BY r.run_id ORDER BY r.run_id DESC
    """).fetchall()
    body = ['<table><thead><tr>'
            '<th>id</th><th>started</th><th>model</th><th>tag</th>'
            '<th class="num">cases</th><th class="num">trials</th>'
            '<th class="num">$ agent</th><th class="num">$ judge</th>'
            '<th>config</th></tr></thead><tbody>']
    for r in rows:
        body.append(
            f'<tr><td><a href="/runs/{r["run_id"]}">{r["run_id"]}</a></td>'
            f'<td>{esc(r["started_at"])}</td>'
            f'<td>{esc(r["agent_model"])}</td>'
            f'<td>{esc(r["tag"]) if r["tag"] else ""}</td>'
            f'<td class="num">{r["cases"]}</td>'
            f'<td class="num">{r["trials"]}</td>'
            f'<td class="num">${r["agent_cost"]:.4f}</td>'
            f'<td class="num">${r["judge_cost"]:.4f}</td>'
            f'<td><code>{r["cfg"]}</code></td></tr>'
        )
    body.append("</tbody></table>")
    return page("runs", "".join(body))


def page_run(conn, run_id: int) -> bytes:
    run = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if run is None:
        return page(f"run {run_id}", "<p>not found</p>")

    cases = conn.execute("""
        SELECT c.case_id, c.input,
               (SELECT COUNT(*) FROM trials WHERE run_id=? AND case_id=c.case_id) AS trials
        FROM cases c
        WHERE c.case_id IN (SELECT case_id FROM trials WHERE run_id=?)
        ORDER BY c.case_id
    """, (run_id, run_id)).fetchall()

    cost = conn.execute("""
        SELECT
          COALESCE(SUM(cost_usd), 0) AS agent_cost,
          COALESCE(SUM(tokens_in), 0) AS tin,
          COALESCE(SUM(tokens_out), 0) AS tout
        FROM trials WHERE run_id=?
    """, (run_id,)).fetchone()
    judge_cost = conn.execute(
        "SELECT judge_name, COALESCE(SUM(judge_cost_usd),0) AS c FROM criterion_verdicts WHERE run_id=? GROUP BY judge_name",
        (run_id,)).fetchall()

    judge_models = json.loads(run["judge_models"] or "{}")
    versions = json.loads(run["judge_prompt_versions"] or "{}")

    body = [
        '<dl class="kvs">',
        f'<dt>started</dt><dd>{esc(run["started_at"])}</dd>',
        f'<dt>ended</dt><dd>{esc(run["ended_at"]) or ""}</dd>',
        f'<dt>agent</dt><dd>{esc(run["agent_model"])}</dd>',
        f'<dt>judges</dt><dd>{esc(", ".join(f"{k} ({v}, v={versions.get(k,"?")})" for k, v in judge_models.items()))}</dd>',
        f'<dt>trials/case</dt><dd>{run["trials_per_case"]}</dd>',
        f'<dt>tag</dt><dd>{esc(run["tag"]) or ""}</dd>',
        f'<dt>config_hash</dt><dd><code>{run["config_hash"]}</code></dd>',
        f'<dt>agent cost</dt><dd>${cost["agent_cost"]:.4f} ({cost["tin"]} in / {cost["tout"]} out)</dd>',
        *[f'<dt>{r["judge_name"]} cost</dt><dd>${r["c"]:.4f}</dd>' for r in judge_cost],
        '</dl>',
        '<h2>cases</h2><table><thead><tr>'
        '<th>case</th><th>input</th>'
        '<th class="num">correct</th><th class="num">faithful</th>'
        '<th>trials</th></tr></thead><tbody>',
    ]
    for c in cases:
        cr = conn.execute("""
            SELECT
              SUM(CASE WHEN judge_name='correctness' AND score=1 THEN 1 ELSE 0 END) AS c_pass,
              SUM(CASE WHEN judge_name='correctness' THEN 1 ELSE 0 END) AS c_n,
              SUM(CASE WHEN judge_name='faithfulness' AND score=1 THEN 1 ELSE 0 END) AS f_pass,
              SUM(CASE WHEN judge_name='faithfulness' THEN 1 ELSE 0 END) AS f_n
            FROM criterion_verdicts
            WHERE run_id=? AND trial_id IN (SELECT trial_id FROM trials WHERE run_id=? AND case_id=?)
        """, (run_id, run_id, c["case_id"])).fetchone()
        trials = conn.execute(
            "SELECT trial_id, trial_idx FROM trials WHERE run_id=? AND case_id=? ORDER BY trial_idx",
            (run_id, c["case_id"])).fetchall()
        trial_links = " ".join(f'<a href="/trials/{t["trial_id"]}">T{t["trial_idx"]}</a>' for t in trials)
        body.append(
            f'<tr><td>{c["case_id"]}</td>'
            f'<td>{esc(trunc(c["input"], 80))}</td>'
            f'<td class="num">{cr["c_pass"]}/{cr["c_n"]}</td>'
            f'<td class="num">{cr["f_pass"]}/{cr["f_n"]}</td>'
            f'<td>{trial_links}</td></tr>'
        )
    body.append('</tbody></table>')
    return page(f"run {run_id}", "".join(body))


def page_trial(conn, trial_id: int) -> bytes:
    t = conn.execute("""
        SELECT t.*, c.input AS case_input, tr.content AS trace
        FROM trials t JOIN cases c ON c.case_id = t.case_id
        LEFT JOIN traces tr ON tr.trace_id = t.trace_id
        WHERE t.trial_id = ?""", (trial_id,)).fetchone()
    if t is None:
        return page(f"trial {trial_id}", "<p>not found</p>")

    verdicts = conn.execute("""
        SELECT v.*, cr.idx AS criterion_idx, cr.text AS criterion_text
        FROM criterion_verdicts v JOIN criteria cr ON cr.criterion_id = v.criterion_id
        WHERE v.trial_id = ? ORDER BY v.judge_name, cr.idx""", (trial_id,)).fetchall()

    tool_calls = conn.execute(
        "SELECT * FROM tool_calls WHERE trial_id = ? ORDER BY idx", (trial_id,)).fetchall()

    body = [
        '<dl class="kvs">',
        f'<dt>run</dt><dd><a href="/runs/{t["run_id"]}">{t["run_id"]}</a></dd>',
        f'<dt>case</dt><dd>{t["case_id"]}</dd>',
        f'<dt>trial idx</dt><dd>{t["trial_idx"]}</dd>',
        f'<dt>latency</dt><dd>{t["latency_ms"] or "-"}ms</dd>',
        f'<dt>tokens</dt><dd>{t["tokens_in"] or 0} in / {t["tokens_out"] or 0} out</dd>',
        f'<dt>cost</dt><dd>${t["cost_usd"] or 0:.4f}</dd>',
        '</dl>',
        '<h2>input</h2><pre>', esc(t["case_input"]), '</pre>',
        '<h2>output</h2><pre>', esc(t["output"]), '</pre>',
    ]

    if tool_calls:
        body.append('<h2>tool calls</h2><table><thead><tr>'
                    '<th>#</th><th>tool</th><th>args</th><th class="num">latency</th></tr></thead><tbody>')
        for tc in tool_calls:
            args = json.loads(tc["args"] or "{}")
            body.append(
                f'<tr><td>{tc["idx"]}</td><td>{esc(tc["tool_name"])}</td>'
                f'<td><code>{esc(args.get("query", json.dumps(args)))}</code></td>'
                f'<td class="num">{tc["latency_ms"] or "-"}ms</td></tr>'
            )
        body.append('</tbody></table>')

    body.append('<h2>verdicts</h2><table><thead><tr>'
                '<th>judge</th><th>#</th><th>criterion</th><th>verdict</th>'
                '<th class="num">conf</th><th>reasoning</th></tr></thead><tbody>')
    for v in verdicts:
        body.append(
            f'<tr><td>{esc(v["judge_name"])}</td><td>{v["criterion_idx"]}</td>'
            f'<td>{esc(trunc(v["criterion_text"], 80))}</td>'
            f'<td>{fmt_pass(v["score"])}</td>'
            f'<td class="num">{v["confidence"]}</td>'
            f'<td>{esc(trunc(v["reasoning"], 240))}</td></tr>'
        )
    body.append('</tbody></table>')

    if t["trace"]:
        body.append('<h2>trace</h2><pre>')
        body.append(esc(trunc(t["trace"], 6000)))
        body.append('</pre>')

    return page(f"trial {trial_id}", "".join(body))


def page_cases(conn) -> bytes:
    cases = conn.execute("SELECT * FROM cases ORDER BY case_id").fetchall()
    body = []
    for c in cases:
        crit = conn.execute(
            "SELECT idx, text FROM criteria WHERE case_id=? AND judge_name='correctness' ORDER BY idx",
            (c["case_id"],)).fetchall()
        body.append(f'<h3>case {c["case_id"]} <small>{esc(c["tags"])}</small></h3>')
        body.append(f'<p>{esc(c["input"])}</p>')
        if c["expected"]:
            body.append(f'<p><small>expected substring: <code>{esc(c["expected"])}</code></small></p>')
        body.append('<ol>')
        for k in crit:
            body.append(f'<li>{esc(k["text"])}</li>')
        body.append('</ol>')
    return page("cases", "".join(body))


# ---------- gold view: the disagreement spotter ----------

def _latest_judge_pr_predictions() -> dict[tuple[int, int], dict]:
    """Parse the most recent judge-pr-correctness-*.md report.
    Returns {(fixed_output_id, criterion_id): {gold, pred, outcome, labeler}}."""
    if not REPORTS_DIR.exists():
        return {}
    candidates = sorted(REPORTS_DIR.glob("judge-pr-correctness-*.md"))
    if not candidates:
        return {}
    text = candidates[-1].read_text()
    out: dict[tuple[int, int], dict] = {}
    for m in re.finditer(
        r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(pass|fail)\s*\|\s*(pass|fail|unknown)\s*\|\s*(TP|FP|TN|FN)\s*\|\s*([^|]+)\s*\|",
        text, re.MULTILINE,
    ):
        fo, cr, gold, pred, outcome, labeler = m.groups()
        out[(int(fo), int(cr))] = {
            "gold": gold, "pred": pred.strip(),
            "outcome": outcome, "labeler": labeler.strip(),
        }
    return out


def page_gold(conn) -> bytes:
    preds = _latest_judge_pr_predictions()
    pred_source = ""
    if preds:
        latest = sorted(REPORTS_DIR.glob("judge-pr-correctness-*.md"))[-1].name
        n_dis = sum(1 for v in preds.values() if v["outcome"] in ("FP", "FN"))
        pred_source = (
            f'<p class="muted">overlay from <code>{latest}</code> '
            f'— {len(preds)} predictions, {n_dis} disagreements (FP/FN highlighted).</p>'
        )
    else:
        pred_source = ('<p class="muted">no judge-pr-correctness-*.md found in results/. '
                       'run <code>uv run python -m evals judge-pr</code> to populate predictions.</p>')

    only_dis = "?only=disagreements" in pred_source  # placeholder

    rows = conn.execute("""
        SELECT fo.fixed_output_id, fo.case_id, fo.agent_output, fo.notes,
               c.input AS case_input
        FROM fixed_outputs fo JOIN cases c ON c.case_id = fo.case_id
        ORDER BY fo.case_id, fo.fixed_output_id
    """).fetchall()

    by_case: dict[int, list] = {}
    for r in rows:
        by_case.setdefault(r["case_id"], []).append(r)

    body = [pred_source]
    for case_id, outputs in by_case.items():
        case_input = outputs[0]["case_input"]
        body.append(f'<h2>case {case_id}</h2>')
        body.append(f'<p>{esc(trunc(case_input, 200))}</p>')

        for fo in outputs:
            crit_rows = conn.execute("""
                SELECT cr.criterion_id, cr.idx, cr.text,
                       g.label AS gold, g.labeler, g.notes AS gold_notes
                FROM criteria cr
                LEFT JOIN gold_labels g
                  ON g.criterion_id = cr.criterion_id
                 AND g.fixed_output_id = ?
                 AND g.judge_name = 'correctness'
                WHERE cr.case_id = ? AND cr.judge_name = 'correctness'
                ORDER BY cr.idx
            """, (fo["fixed_output_id"], fo["case_id"])).fetchall()

            body.append(f'<h3>fixed_output {fo["fixed_output_id"]}'
                        f' <small>{esc(fo["notes"]) if fo["notes"] else ""}</small></h3>')
            body.append(f'<pre>{esc(trunc(fo["agent_output"], 600))}</pre>')
            body.append('<table><thead><tr>'
                        '<th>#</th><th>criterion</th><th>gold</th><th>pred</th>'
                        '<th>outcome</th><th>labeler</th></tr></thead><tbody>')
            for cr in crit_rows:
                pred_info = preds.get((fo["fixed_output_id"], cr["criterion_id"]))
                row_class = ""
                if pred_info and pred_info["outcome"] in ("FP", "FN"):
                    row_class = ' class="disagree"'
                gold_str = ("pass" if cr["gold"] == 1 else
                            "fail" if cr["gold"] == 0 else "—")
                pred_cell = "—"
                outcome_cell = ""
                if pred_info:
                    pred_cell = pred_info["pred"]
                    outcome_cell = pred_info["outcome"]
                body.append(
                    f'<tr{row_class}><td>{cr["idx"]}</td>'
                    f'<td>{esc(trunc(cr["text"], 120))}</td>'
                    f'<td>{gold_str}</td>'
                    f'<td>{pred_cell}</td>'
                    f'<td>{outcome_cell}</td>'
                    f'<td>{esc(cr["labeler"]) or "—"}</td></tr>'
                )
            body.append('</tbody></table>')
    return page("gold labels", "".join(body))


# ---------- HTTP plumbing ----------

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        try:
            conn = db.connect()
            try:
                if path == "/":
                    body = page_index(conn)
                elif path == "/runs":
                    body = page_runs(conn)
                elif (m := re.fullmatch(r"/runs/(\d+)", path)):
                    body = page_run(conn, int(m.group(1)))
                elif (m := re.fullmatch(r"/trials/(\d+)", path)):
                    body = page_trial(conn, int(m.group(1)))
                elif path == "/cases":
                    body = page_cases(conn)
                elif path == "/gold":
                    body = page_gold(conn)
                else:
                    self.send_error(404, "not found"); return
            finally:
                conn.close()
        except Exception as e:
            self.send_error(500, f"{type(e).__name__}: {e}"); raise

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} {fmt % args}\n")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"serving evals.db at http://localhost:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
