import { db } from "./db";

export type Case = {
  case_id: number;
  input: string;
  expected: string | null;
  tags: string;
  created_at: string;
  archived_at: string | null;
};

export type Criterion = {
  criterion_id: number;
  case_id: number | null;
  judge_name: string;
  idx: number;
  text: string;
};

export type FixedOutput = {
  fixed_output_id: number;
  case_id: number;
  agent_output: string;
  notes: string | null;
  trace: string | null;
  source: string | null;
  created_at: string;
};

export type GoldLabel = {
  gold_label_id: number;
  criterion_id: number;
  fixed_output_id: number;
  judge_name: string;
  label: number; // 0 or 1
  labeler: string;
  notes: string | null;
  created_at: string;
};

export function listCases(): Case[] {
  return db()
    .prepare(
      `SELECT case_id, input, expected, tags, created_at, archived_at
       FROM cases ORDER BY case_id`,
    )
    .all() as Case[];
}

export function getCase(caseId: number): Case | undefined {
  return db()
    .prepare(`SELECT * FROM cases WHERE case_id = ?`)
    .get(caseId) as Case | undefined;
}

export function listCriteriaForCase(caseId: number): Criterion[] {
  return db()
    .prepare(
      `SELECT criterion_id, case_id, judge_name, idx, text
       FROM criteria WHERE case_id = ? ORDER BY judge_name, idx`,
    )
    .all(caseId) as Criterion[];
}

export function getFaithfulnessCriterion(): Criterion | undefined {
  return db()
    .prepare(
      `SELECT criterion_id, case_id, judge_name, idx, text
       FROM criteria WHERE case_id IS NULL AND judge_name = 'faithfulness' LIMIT 1`,
    )
    .get() as Criterion | undefined;
}

export function listFixedOutputs(): (FixedOutput & { case_input: string })[] {
  return db()
    .prepare(
      `SELECT fo.*, c.input AS case_input
       FROM fixed_outputs fo
       JOIN cases c ON c.case_id = fo.case_id
       ORDER BY fo.case_id, fo.fixed_output_id`,
    )
    .all() as (FixedOutput & { case_input: string })[];
}

export function getFixedOutput(id: number): (FixedOutput & { case_input: string }) | undefined {
  return db()
    .prepare(
      `SELECT fo.*, c.input AS case_input
       FROM fixed_outputs fo
       JOIN cases c ON c.case_id = fo.case_id
       WHERE fo.fixed_output_id = ?`,
    )
    .get(id) as (FixedOutput & { case_input: string }) | undefined;
}

export function getGoldLabelsForFixedOutput(id: number): GoldLabel[] {
  return db()
    .prepare(
      `SELECT * FROM gold_labels WHERE fixed_output_id = ?`,
    )
    .all(id) as GoldLabel[];
}

export type GoldLabelStat = {
  judge_name: string;
  total: number;
  pass: number;
  fail: number;
  hand: number;
  auto: number;
};

export type JudgePrRun = {
  judge_pr_run_id: number;
  judge_name: string;
  judge_model: string;
  prompt_version: string;
  started_at: string;
  elapsed_ms: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  total: number;
  auto_labeled: number;
  precision_pct: number;
  recall_pct: number;
  f1_pct: number;
  accuracy_pct: number;
};

export type JudgePrRow = {
  judge_pr_row_id: number;
  judge_pr_run_id: number;
  fixed_output_id: number;
  criterion_id: number;
  case_id: number;
  gold: string;
  predicted: string;
  outcome: string;
  labeler: string;
};

export function listJudgePrRuns(): JudgePrRun[] {
  return db()
    .prepare(`SELECT * FROM judge_pr_runs ORDER BY started_at DESC`)
    .all() as JudgePrRun[];
}

export function latestJudgePrRun(judgeName: string): JudgePrRun | undefined {
  return db()
    .prepare(
      `SELECT * FROM judge_pr_runs WHERE judge_name = ?
       ORDER BY started_at DESC LIMIT 1`,
    )
    .get(judgeName) as JudgePrRun | undefined;
}

export function getJudgePrRows(prRunId: number): (JudgePrRow & { criterion_text: string; case_input: string })[] {
  return db()
    .prepare(
      `SELECT r.*, c.text AS criterion_text, ca.input AS case_input
       FROM judge_pr_rows r
       JOIN criteria c ON c.criterion_id = r.criterion_id
       JOIN cases ca ON ca.case_id = r.case_id
       WHERE r.judge_pr_run_id = ?
       ORDER BY r.outcome, r.case_id, r.criterion_id`,
    )
    .all(prRunId) as (JudgePrRow & { criterion_text: string; case_input: string })[];
}

export type JudgePrompt = {
  judge_prompt_id: number;
  judge_name: string;
  version: string;
  template: string;
  notes: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
};

// Placeholders the judge code computes; the UI shows these so users know
// what variables are available in each template.
export const PLACEHOLDERS: Record<string, string[]> = {
  correctness: [
    "current_date",
    "numbered_criteria",
    "agent_input",
    "agent_output",
    "reference_section",
  ],
  faithfulness: ["current_date", "agent_input", "agent_output", "evidence_block"],
};

export type Run = {
  run_id: number;
  started_at: string;
  ended_at: string | null;
  agent_model: string;
  agent_system_prompt: string;
  trials_per_case: number;
  judge_models: string;
  judge_prompt_versions: string;
  judge_temperatures: string;
  config_hash: string;
  tag: string | null;
};

export type Trial = {
  trial_id: number;
  run_id: number;
  case_id: number;
  trial_idx: number;
  output: string;
  trace_id: number | null;
  latency_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  cost_usd: number | null;
  created_at: string;
  reviewer_notes: string | null;
  error: string | null;
};

export type Verdict = {
  verdict_id: number;
  run_id: number;
  trial_id: number;
  criterion_id: number;
  judge_name: string;
  judge_model: string;
  score: number | null;
  confidence: number;
  reasoning: string;
  judge_latency_ms: number | null;
  judge_tokens_in: number | null;
  judge_tokens_out: number | null;
  judge_cost_usd: number | null;
  created_at: string;
  reviewer_notes: string | null;
  failure_mode: string | null;
  reviewed_at: string | null;
};

export { FAILURE_MODES, type FailureMode } from "./review";

export type ToolCall = {
  tool_call_id: number;
  trial_id: number;
  idx: number;
  tool_name: string;
  args: string;
  result: string;
  latency_ms: number | null;
  tokens: number | null;
};

export function listRuns(): (Run & { trial_count: number; total_cost: number | null; mean_correctness: number | null })[] {
  return db()
    .prepare(
      `SELECT r.*,
              (SELECT COUNT(*) FROM trials t WHERE t.run_id = r.run_id) AS trial_count,
              (SELECT COALESCE(SUM(cost_usd), 0) FROM trials t WHERE t.run_id = r.run_id) +
              (SELECT COALESCE(SUM(judge_cost_usd), 0) FROM criterion_verdicts v WHERE v.run_id = r.run_id) AS total_cost,
              (SELECT AVG(CAST(score AS REAL)) FROM criterion_verdicts v
                 WHERE v.run_id = r.run_id AND v.judge_name = 'correctness' AND v.score IS NOT NULL) AS mean_correctness
       FROM runs r ORDER BY r.run_id DESC`,
    )
    .all() as (Run & { trial_count: number; total_cost: number | null; mean_correctness: number | null })[];
}

export function getRun(id: number): Run | undefined {
  return db().prepare(`SELECT * FROM runs WHERE run_id = ?`).get(id) as Run | undefined;
}

export function listTrialsForRun(runId: number): (Trial & { case_input: string })[] {
  return db()
    .prepare(
      `SELECT t.*, c.input AS case_input
       FROM trials t JOIN cases c ON c.case_id = t.case_id
       WHERE t.run_id = ?
       ORDER BY t.case_id, t.trial_idx`,
    )
    .all(runId) as (Trial & { case_input: string })[];
}

export function caseRollupForRun(runId: number): {
  case_id: number;
  case_input: string;
  trials: number;
  correctness_pass: number;
  correctness_total: number;
  faithfulness_pass: number;
  faithfulness_total: number;
  tool_use_pass: number;
  tool_use_total: number;
  p50_latency_ms: number | null;
  total_cost: number;
}[] {
  return db()
    .prepare(
      `SELECT c.case_id, c.input AS case_input,
              COUNT(DISTINCT t.trial_id) AS trials,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score=1 THEN 1 ELSE 0 END) AS correctness_pass,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS correctness_total,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score=1 THEN 1 ELSE 0 END) AS faithfulness_pass,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS faithfulness_total,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score=1 THEN 1 ELSE 0 END) AS tool_use_pass,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS tool_use_total,
              (SELECT AVG(latency_ms) FROM trials t2 WHERE t2.run_id = ? AND t2.case_id = c.case_id) AS p50_latency_ms,
              COALESCE((SELECT SUM(cost_usd) FROM trials t2 WHERE t2.run_id = ? AND t2.case_id = c.case_id), 0) +
              COALESCE((SELECT SUM(judge_cost_usd) FROM criterion_verdicts v2 WHERE v2.run_id = ? AND v2.trial_id IN
                          (SELECT trial_id FROM trials WHERE run_id = ? AND case_id = c.case_id)), 0) AS total_cost
       FROM cases c
       JOIN trials t ON t.case_id = c.case_id AND t.run_id = ?
       LEFT JOIN criterion_verdicts v ON v.trial_id = t.trial_id
       GROUP BY c.case_id, c.input
       ORDER BY c.case_id`,
    )
    .all(runId, runId, runId, runId, runId) as ReturnType<typeof caseRollupForRun>;
}

export function getTrial(id: number): (Trial & { case_input: string; run_started_at: string }) | undefined {
  return db()
    .prepare(
      `SELECT t.*, c.input AS case_input, r.started_at AS run_started_at
       FROM trials t
       JOIN cases c ON c.case_id = t.case_id
       JOIN runs r ON r.run_id = t.run_id
       WHERE t.trial_id = ?`,
    )
    .get(id) as (Trial & { case_input: string; run_started_at: string }) | undefined;
}

export function getTrace(id: number): { trace_id: number; content: string } | undefined {
  return db().prepare(`SELECT trace_id, content FROM traces WHERE trace_id = ?`).get(id) as
    | { trace_id: number; content: string }
    | undefined;
}

export function getVerdictsForTrial(trialId: number): (Verdict & { criterion_text: string; criterion_idx: number })[] {
  return db()
    .prepare(
      `SELECT v.*, c.text AS criterion_text, c.idx AS criterion_idx
       FROM criterion_verdicts v
       JOIN criteria c ON c.criterion_id = v.criterion_id
       WHERE v.trial_id = ?
       ORDER BY v.judge_name, c.idx`,
    )
    .all(trialId) as (Verdict & { criterion_text: string; criterion_idx: number })[];
}

export function getToolCallsForTrial(trialId: number): ToolCall[] {
  return db()
    .prepare(`SELECT * FROM tool_calls WHERE trial_id = ? ORDER BY idx`)
    .all(trialId) as ToolCall[];
}

export function getPromptIdByJudgeAndVersion(judgeName: string, version: string): number | undefined {
  const row = db()
    .prepare(`SELECT judge_prompt_id FROM judge_prompts WHERE judge_name = ? AND version = ?`)
    .get(judgeName, version) as { judge_prompt_id: number } | undefined;
  return row?.judge_prompt_id;
}

export function listJudgeNames(): string[] {
  const rows = db()
    .prepare(`SELECT DISTINCT judge_name FROM judge_prompts ORDER BY judge_name`)
    .all() as { judge_name: string }[];
  return rows.map((r) => r.judge_name);
}

export function listPromptsForJudge(judgeName: string): JudgePrompt[] {
  return db()
    .prepare(
      `SELECT * FROM judge_prompts WHERE judge_name = ?
       ORDER BY is_active DESC, judge_prompt_id DESC`,
    )
    .all(judgeName) as JudgePrompt[];
}

export function getPrompt(id: number): JudgePrompt | undefined {
  return db()
    .prepare(`SELECT * FROM judge_prompts WHERE judge_prompt_id = ?`)
    .get(id) as JudgePrompt | undefined;
}

export function activePromptByJudge(): Record<string, JudgePrompt> {
  const rows = db()
    .prepare(`SELECT * FROM judge_prompts WHERE is_active = 1`)
    .all() as JudgePrompt[];
  return Object.fromEntries(rows.map((r) => [r.judge_name, r]));
}

export function promptUsedByRunCount(judgeName: string, version: string): number {
  // Count runs whose judge_prompt_versions JSON has this judge=version pair.
  const rows = db()
    .prepare(`SELECT judge_prompt_versions FROM runs`)
    .all() as { judge_prompt_versions: string }[];
  let n = 0;
  for (const r of rows) {
    try {
      const map = JSON.parse(r.judge_prompt_versions) as Record<string, string>;
      if (map[judgeName] === version) n++;
    } catch {
      // ignore malformed
    }
  }
  return n;
}

// --- Run comparison ----------------------------------------------------------

const Z_95 = 1.959964;

export function wilsonCI(passN: number, total: number): { p: number; lo: number; hi: number } {
  if (total === 0) return { p: 0, lo: 0, hi: 0 };
  const p = passN / total;
  const z = Z_95;
  const denom = 1 + (z * z) / total;
  const center = (p + (z * z) / (2 * total)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / total + (z * z) / (4 * total * total))) / denom;
  return { p, lo: Math.max(0, center - half), hi: Math.min(1, center + half) };
}

export type CriterionGroup = {
  case_id: number | null;
  case_input: string | null;
  judge_name: string;
  idx: number;
  text: string;
  pass_n: number;
  total: number;
};

function aggregateCriteria(runId: number): Map<string, CriterionGroup> {
  const rows = db()
    .prepare(
      `SELECT cr.case_id, cr.idx, cr.text, v.judge_name, ca.input AS case_input,
              SUM(CASE WHEN v.score = 1 THEN 1 ELSE 0 END) AS pass_n,
              COUNT(v.verdict_id) AS total
       FROM criterion_verdicts v
       JOIN criteria cr ON cr.criterion_id = v.criterion_id
       LEFT JOIN cases ca ON ca.case_id = cr.case_id
       WHERE v.run_id = ?
       GROUP BY cr.case_id, cr.idx, v.judge_name`,
    )
    .all(runId) as {
    case_id: number | null;
    idx: number;
    text: string;
    judge_name: string;
    case_input: string | null;
    pass_n: number;
    total: number;
  }[];
  const out = new Map<string, CriterionGroup>();
  for (const r of rows) {
    out.set(`${r.case_id ?? "null"}|${r.judge_name}|${r.idx}`, r);
  }
  return out;
}

type CaseRollupRow = ReturnType<typeof caseRollupForRun>[number];

export type CaseDelta = {
  case_id: number;
  case_input: string;
  a: CaseRollupRow | null;
  b: CaseRollupRow | null;
  judges: {
    judge_name: string;
    a_pass: number; a_total: number;
    b_pass: number; b_total: number;
    delta: number;
    significant: boolean;
  }[];
  latency_a: number | null;
  latency_b: number | null;
  latency_delta: number | null;
  cost_a: number;
  cost_b: number;
  cost_delta: number;
};

export type CriterionDelta = {
  case_id: number | null;
  case_input: string | null;
  judge_name: string;
  idx: number;
  text: string;
  a_pass: number; a_total: number;
  b_pass: number; b_total: number;
  a_p: number; a_lo: number; a_hi: number;
  b_p: number; b_lo: number; b_hi: number;
  delta: number;
  significant: boolean;
};

export type RunComparison = {
  a: Run;
  b: Run;
  configHashDiffers: boolean;
  fieldDiffs: string[];
  cases: CaseDelta[];
  criteria: CriterionDelta[];
  failureModeDeltas: FailureModeDelta[];
};

const COMPARED_FIELDS: (keyof Run)[] = [
  "agent_model",
  "agent_system_prompt",
  "trials_per_case",
  "judge_models",
  "judge_prompt_versions",
  "judge_temperatures",
  "config_hash",
  "tag",
];

const JUDGE_NAMES = ["correctness", "faithfulness", "tool_use"] as const;

export function compareRuns(runA: number, runB: number): RunComparison | null {
  const a = getRun(runA);
  const b = getRun(runB);
  if (!a || !b) return null;

  const fieldDiffs = COMPARED_FIELDS.filter((f) => a[f] !== b[f]).map(String);

  const rollupA = caseRollupForRun(runA);
  const rollupB = caseRollupForRun(runB);
  const aById = new Map(rollupA.map((r) => [r.case_id, r]));
  const bById = new Map(rollupB.map((r) => [r.case_id, r]));
  const allCaseIds = Array.from(new Set([...aById.keys(), ...bById.keys()])).sort((x, y) => x - y);

  const cases: CaseDelta[] = allCaseIds.map((cid) => {
    const ar = aById.get(cid) ?? null;
    const br = bById.get(cid) ?? null;
    const judges = JUDGE_NAMES.map((j) => {
      const aPass = ar ? (ar as any)[`${j}_pass`] ?? 0 : 0;
      const aTotal = ar ? (ar as any)[`${j}_total`] ?? 0 : 0;
      const bPass = br ? (br as any)[`${j}_pass`] ?? 0 : 0;
      const bTotal = br ? (br as any)[`${j}_total`] ?? 0 : 0;
      const ap = aTotal ? aPass / aTotal : 0;
      const bp = bTotal ? bPass / bTotal : 0;
      const aCi = wilsonCI(aPass, aTotal);
      const bCi = wilsonCI(bPass, bTotal);
      const significant =
        aTotal > 0 && bTotal > 0 && (aCi.hi < bCi.lo || bCi.hi < aCi.lo);
      return {
        judge_name: j,
        a_pass: aPass, a_total: aTotal,
        b_pass: bPass, b_total: bTotal,
        delta: bp - ap,
        significant,
      };
    });
    return {
      case_id: cid,
      case_input: (ar?.case_input ?? br?.case_input ?? "") as string,
      a: ar,
      b: br,
      judges,
      latency_a: ar?.p50_latency_ms ?? null,
      latency_b: br?.p50_latency_ms ?? null,
      latency_delta:
        ar?.p50_latency_ms != null && br?.p50_latency_ms != null
          ? br.p50_latency_ms - ar.p50_latency_ms
          : null,
      cost_a: ar?.total_cost ?? 0,
      cost_b: br?.total_cost ?? 0,
      cost_delta: (br?.total_cost ?? 0) - (ar?.total_cost ?? 0),
    };
  });

  const aMap = aggregateCriteria(runA);
  const bMap = aggregateCriteria(runB);
  const allKeys = Array.from(new Set([...aMap.keys(), ...bMap.keys()]));
  const criteria: CriterionDelta[] = allKeys
    .map((k) => {
      const ag = aMap.get(k);
      const bg = bMap.get(k);
      const ref = ag ?? bg!;
      const aPass = ag?.pass_n ?? 0;
      const aTotal = ag?.total ?? 0;
      const bPass = bg?.pass_n ?? 0;
      const bTotal = bg?.total ?? 0;
      const aCi = wilsonCI(aPass, aTotal);
      const bCi = wilsonCI(bPass, bTotal);
      const significant =
        aTotal > 0 && bTotal > 0 && (aCi.hi < bCi.lo || bCi.hi < aCi.lo);
      return {
        case_id: ref.case_id,
        case_input: ref.case_input,
        judge_name: ref.judge_name,
        idx: ref.idx,
        text: ref.text,
        a_pass: aPass, a_total: aTotal,
        b_pass: bPass, b_total: bTotal,
        a_p: aCi.p, a_lo: aCi.lo, a_hi: aCi.hi,
        b_p: bCi.p, b_lo: bCi.lo, b_hi: bCi.hi,
        delta: bCi.p - aCi.p,
        significant,
      };
    })
    .sort((x, y) => {
      // None case_id (global) last; then case_id, judge, idx
      const xn = x.case_id == null ? 1 : 0;
      const yn = y.case_id == null ? 1 : 0;
      if (xn !== yn) return xn - yn;
      if ((x.case_id ?? 0) !== (y.case_id ?? 0)) return (x.case_id ?? 0) - (y.case_id ?? 0);
      if (x.judge_name !== y.judge_name) return x.judge_name < y.judge_name ? -1 : 1;
      return x.idx - y.idx;
    });

  return {
    a,
    b,
    configHashDiffers: a.config_hash !== b.config_hash,
    fieldDiffs,
    cases,
    criteria,
    failureModeDeltas: failureModeDeltas(runA, runB),
  };
}

export type CaseReviewCount = { case_id: number; reviewed: number };

export function reviewedCountsForRun(runId: number): Map<number, number> {
  const rows = db()
    .prepare(
      `SELECT t.case_id AS case_id, COUNT(*) AS reviewed
       FROM criterion_verdicts v
       JOIN trials t ON t.trial_id = v.trial_id
       WHERE v.run_id = ? AND v.reviewed_at IS NOT NULL
       GROUP BY t.case_id`,
    )
    .all(runId) as CaseReviewCount[];
  return new Map(rows.map((r) => [r.case_id, r.reviewed]));
}

export type FailureModeCount = { failure_mode: string; n: number };

export function failureModeCountsForRun(runId: number): FailureModeCount[] {
  return db()
    .prepare(
      `SELECT failure_mode, COUNT(*) AS n
       FROM criterion_verdicts
       WHERE run_id = ? AND failure_mode IS NOT NULL
       GROUP BY failure_mode
       ORDER BY n DESC, failure_mode`,
    )
    .all(runId) as FailureModeCount[];
}

export type FailureModeDelta = {
  case_id: number | null;
  case_input: string | null;
  judge_name: string;
  idx: number;
  text: string;
  a_modes: string[];
  b_modes: string[];
};

function failureModeRowsForRun(runId: number) {
  return db()
    .prepare(
      `SELECT cr.case_id, cr.idx, cr.text, v.judge_name, ca.input AS case_input, v.failure_mode
       FROM criterion_verdicts v
       JOIN criteria cr ON cr.criterion_id = v.criterion_id
       LEFT JOIN cases ca ON ca.case_id = cr.case_id
       WHERE v.run_id = ? AND v.failure_mode IS NOT NULL`,
    )
    .all(runId) as {
    case_id: number | null;
    idx: number;
    text: string;
    judge_name: string;
    case_input: string | null;
    failure_mode: string;
  }[];
}

function bucketModes(rows: ReturnType<typeof failureModeRowsForRun>) {
  const out = new Map<string, { ref: (typeof rows)[number]; modes: Set<string> }>();
  for (const r of rows) {
    const k = `${r.case_id ?? "null"}|${r.judge_name}|${r.idx}`;
    if (!out.has(k)) out.set(k, { ref: r, modes: new Set() });
    out.get(k)!.modes.add(r.failure_mode);
  }
  return out;
}

export function failureModeDeltas(runA: number, runB: number): FailureModeDelta[] {
  const a = bucketModes(failureModeRowsForRun(runA));
  const b = bucketModes(failureModeRowsForRun(runB));
  const keys = Array.from(new Set([...a.keys(), ...b.keys()]));
  const out: FailureModeDelta[] = [];
  for (const k of keys) {
    const ag = a.get(k);
    const bg = b.get(k);
    const aModes = ag ? Array.from(ag.modes).sort() : [];
    const bModes = bg ? Array.from(bg.modes).sort() : [];
    if (aModes.join(",") === bModes.join(",")) continue;
    const ref = (ag ?? bg)!.ref;
    out.push({
      case_id: ref.case_id,
      case_input: ref.case_input,
      judge_name: ref.judge_name,
      idx: ref.idx,
      text: ref.text,
      a_modes: aModes,
      b_modes: bModes,
    });
  }
  return out.sort((x, y) => {
    const xn = x.case_id == null ? 1 : 0;
    const yn = y.case_id == null ? 1 : 0;
    if (xn !== yn) return xn - yn;
    if ((x.case_id ?? 0) !== (y.case_id ?? 0)) return (x.case_id ?? 0) - (y.case_id ?? 0);
    if (x.judge_name !== y.judge_name) return x.judge_name < y.judge_name ? -1 : 1;
    return x.idx - y.idx;
  });
}

export function goldLabelStats(): GoldLabelStat[] {
  return db()
    .prepare(
      `SELECT judge_name,
              COUNT(*) AS total,
              SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) AS pass,
              SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) AS fail,
              SUM(CASE WHEN labeler = 'auto-from-case-level' THEN 0 ELSE 1 END) AS hand,
              SUM(CASE WHEN labeler = 'auto-from-case-level' THEN 1 ELSE 0 END) AS auto
       FROM gold_labels GROUP BY judge_name ORDER BY judge_name`,
    )
    .all() as GoldLabelStat[];
}

export type CaseIndexRow = {
  case_id: number;
  input: string;
  tags: string;
  criteria_count: number;
  fixed_output_count: number;
  correctness_pass: number;
  correctness_total: number;
  correctness_auto: number;
  faithfulness_pass: number;
  faithfulness_total: number;
  faithfulness_auto: number;
  needs_labels: number; // 1 if any case-scoped criterion has zero gold_labels
  last_trial_run_id: number | null;
  last_trial_id: number | null;
  last_trial_started: string | null;
  last_trial_pass: number | null;   // pass count across judges for that trial
  last_trial_total: number | null;
};

export function listCaseIndexRows(): CaseIndexRow[] {
  const rows = db()
    .prepare(
      `WITH lbl AS (
         SELECT cr.case_id, gl.judge_name,
                SUM(CASE WHEN gl.label = 1 THEN 1 ELSE 0 END) AS pass,
                SUM(CASE WHEN gl.label IS NOT NULL THEN 1 ELSE 0 END) AS total,
                SUM(CASE WHEN gl.labeler = 'auto-from-case-level' THEN 1 ELSE 0 END) AS auto
         FROM gold_labels gl
         JOIN criteria cr ON cr.criterion_id = gl.criterion_id
         GROUP BY cr.case_id, gl.judge_name
       ),
       last_trial AS (
         SELECT t.case_id, t.trial_id, t.run_id, t.created_at AS started
         FROM trials t
         JOIN (
           SELECT case_id, MAX(trial_id) AS max_id FROM trials GROUP BY case_id
         ) m ON m.case_id = t.case_id AND m.max_id = t.trial_id
       ),
       last_verdicts AS (
         SELECT v.trial_id,
                SUM(CASE WHEN v.score = 1 THEN 1 ELSE 0 END) AS pass,
                SUM(CASE WHEN v.score IS NOT NULL THEN 1 ELSE 0 END) AS total
         FROM criterion_verdicts v
         JOIN last_trial lt ON lt.trial_id = v.trial_id
         GROUP BY v.trial_id
       ),
       crit_counts AS (
         SELECT case_id, COUNT(*) AS n FROM criteria WHERE case_id IS NOT NULL GROUP BY case_id
       ),
       fo_counts AS (
         SELECT case_id, COUNT(*) AS n FROM fixed_outputs GROUP BY case_id
       ),
       missing AS (
         SELECT cr.case_id,
                SUM(CASE WHEN NOT EXISTS (
                       SELECT 1 FROM gold_labels gl WHERE gl.criterion_id = cr.criterion_id
                ) THEN 1 ELSE 0 END) AS missing_n
         FROM criteria cr
         WHERE cr.case_id IS NOT NULL
         GROUP BY cr.case_id
       )
       SELECT c.case_id, c.input, c.tags,
              COALESCE(cc.n, 0) AS criteria_count,
              COALESCE(fc.n, 0) AS fixed_output_count,
              COALESCE((SELECT pass FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_pass,
              COALESCE((SELECT total FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_total,
              COALESCE((SELECT auto FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='correctness'), 0) AS correctness_auto,
              COALESCE((SELECT pass FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_pass,
              COALESCE((SELECT total FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_total,
              COALESCE((SELECT auto FROM lbl WHERE lbl.case_id = c.case_id AND judge_name='faithfulness'), 0) AS faithfulness_auto,
              CASE WHEN COALESCE(m.missing_n, 0) > 0 THEN 1 ELSE 0 END AS needs_labels,
              lt.run_id AS last_trial_run_id,
              lt.trial_id AS last_trial_id,
              lt.started AS last_trial_started,
              lv.pass AS last_trial_pass,
              lv.total AS last_trial_total
       FROM cases c
       LEFT JOIN crit_counts cc ON cc.case_id = c.case_id
       LEFT JOIN fo_counts fc ON fc.case_id = c.case_id
       LEFT JOIN missing m ON m.case_id = c.case_id
       LEFT JOIN last_trial lt ON lt.case_id = c.case_id
       LEFT JOIN last_verdicts lv ON lv.trial_id = lt.trial_id
       ORDER BY c.case_id`,
    )
    .all() as CaseIndexRow[];
  return rows;
}

export type CaseTrialHistoryRow = {
  trial_id: number;
  run_id: number;
  trial_idx: number;
  started_at: string;
  latency_ms: number | null;
  cost_usd: number | null;
  correctness_pass: number;
  correctness_total: number;
  faithfulness_pass: number;
  faithfulness_total: number;
  tool_use_pass: number;
  tool_use_total: number;
};

export function listTrialHistoryForCase(caseId: number): CaseTrialHistoryRow[] {
  return db()
    .prepare(
      `SELECT t.trial_id, t.run_id, t.trial_idx, t.created_at AS started_at,
              t.latency_ms, t.cost_usd,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score=1 THEN 1 ELSE 0 END) AS correctness_pass,
              SUM(CASE WHEN v.judge_name='correctness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS correctness_total,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score=1 THEN 1 ELSE 0 END) AS faithfulness_pass,
              SUM(CASE WHEN v.judge_name='faithfulness' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS faithfulness_total,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score=1 THEN 1 ELSE 0 END) AS tool_use_pass,
              SUM(CASE WHEN v.judge_name='tool_use' AND v.score IS NOT NULL THEN 1 ELSE 0 END) AS tool_use_total
       FROM trials t
       LEFT JOIN criterion_verdicts v ON v.trial_id = t.trial_id
       WHERE t.case_id = ?
       GROUP BY t.trial_id
       ORDER BY t.trial_id DESC`,
    )
    .all(caseId) as CaseTrialHistoryRow[];
}

export type RunSummary = {
  run_id: number;
  agent_model: string;
  case_count: number;
  trial_count: number;
  total_cost: number;
  p50_latency_ms: number | null;
  p95_latency_ms: number | null;
  pass: number;
  total: number;
};

export function getRunSummary(runId: number): RunSummary | undefined {
  const base = db()
    .prepare(
      `SELECT r.run_id, r.agent_model,
              (SELECT COUNT(DISTINCT case_id) FROM trials WHERE run_id = r.run_id) AS case_count,
              (SELECT COUNT(*) FROM trials WHERE run_id = r.run_id) AS trial_count,
              COALESCE((SELECT SUM(cost_usd) FROM trials WHERE run_id = r.run_id), 0)
                + COALESCE((SELECT SUM(judge_cost_usd) FROM criterion_verdicts WHERE run_id = r.run_id), 0) AS total_cost,
              (SELECT SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) FROM criterion_verdicts WHERE run_id = r.run_id) AS pass,
              (SELECT SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) FROM criterion_verdicts WHERE run_id = r.run_id) AS total
       FROM runs r WHERE r.run_id = ?`,
    )
    .get(runId) as Omit<RunSummary, "p50_latency_ms" | "p95_latency_ms"> | undefined;
  if (!base) return undefined;
  const latencies = (
    db()
      .prepare(`SELECT latency_ms FROM trials WHERE run_id = ? AND latency_ms IS NOT NULL ORDER BY latency_ms`)
      .all(runId) as { latency_ms: number }[]
  ).map((r) => r.latency_ms);
  const pct = (p: number) =>
    latencies.length ? latencies[Math.min(latencies.length - 1, Math.floor(latencies.length * p))] : null;
  return { ...base, p50_latency_ms: pct(0.5), p95_latency_ms: pct(0.95) };
}
