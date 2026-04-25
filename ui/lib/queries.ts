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
