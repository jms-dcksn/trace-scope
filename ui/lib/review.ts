export const FAILURE_MODES = [
  "agent-error",
  "judge-too-strict",
  "judge-too-lenient",
  "gold-wrong",
  "criterion-ambiguous",
  "other",
] as const;
export type FailureMode = (typeof FAILURE_MODES)[number];
