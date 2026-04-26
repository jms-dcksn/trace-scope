"""Shared tool_use rule expansion.

Both the seeder (which materializes `criteria` rows for `judge_name='tool_use'`)
and ToolUseJudge (which evaluates a trial's tool_calls) use this expansion so
criterion order matches verdict order.

A `payload` is the dict stored in `case_expectations.value` (JSON). Supported
keys:
  - min_calls: int
  - max_calls: int
  - must_include_substrings: list[str]   # one criterion per substring
  - no_duplicate_queries: bool
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriterionSpec:
    text: str
    kind: str          # 'min_calls' | 'max_calls' | 'substring' | 'no_duplicate_queries'
    param: object


def expand_payload(payload: dict) -> list[CriterionSpec]:
    """Deterministic expansion: order is stable so DB idx matches judge output."""
    specs: list[CriterionSpec] = []
    if "min_calls" in payload:
        n = int(payload["min_calls"])
        specs.append(CriterionSpec(
            text=f"made at least {n} tool call(s)",
            kind="min_calls",
            param=n,
        ))
    if "max_calls" in payload:
        n = int(payload["max_calls"])
        specs.append(CriterionSpec(
            text=f"made at most {n} tool call(s)",
            kind="max_calls",
            param=n,
        ))
    for sub in payload.get("must_include_substrings") or []:
        specs.append(CriterionSpec(
            text=f"at least one query contains '{sub}' (case-insensitive)",
            kind="substring",
            param=sub,
        ))
    if payload.get("no_duplicate_queries"):
        specs.append(CriterionSpec(
            text="no duplicate queries across tool calls",
            kind="no_duplicate_queries",
            param=None,
        ))
    return specs


def evaluate_spec(spec: CriterionSpec, queries: list[str]) -> tuple[str, str]:
    """Returns (label, reasoning). label in {'pass', 'fail'}."""
    n = len(queries)
    if spec.kind == "min_calls":
        ok = n >= spec.param
        return ("pass" if ok else "fail",
                f"{n} call(s) made; required >= {spec.param}")
    if spec.kind == "max_calls":
        ok = n <= spec.param
        return ("pass" if ok else "fail",
                f"{n} call(s) made; allowed <= {spec.param}")
    if spec.kind == "substring":
        sub = str(spec.param).lower()
        hit = next((q for q in queries if sub in q.lower()), None)
        if hit:
            return "pass", f"matched in query: {hit!r}"
        return "fail", f"no query contained {spec.param!r}"
    if spec.kind == "no_duplicate_queries":
        norm = [q.strip().lower() for q in queries]
        dupes = len(norm) - len(set(norm))
        if dupes == 0:
            return "pass", f"{n} unique query/queries"
        return "fail", f"{dupes} duplicate query/queries"
    return "fail", f"unknown rule kind {spec.kind!r}"
