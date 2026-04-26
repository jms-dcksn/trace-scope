"use client";

import { useState, useTransition } from "react";
import { FAILURE_MODES } from "@/lib/review";
import { saveTrialReview, saveVerdictReview } from "../../../actions";

export function VerdictReview({
  verdictId,
  runId,
  trialId,
  initialNotes,
  initialMode,
  reviewedAt,
}: {
  verdictId: number;
  runId: number;
  trialId: number;
  initialNotes: string | null;
  initialMode: string | null;
  reviewedAt: string | null;
}) {
  const reviewed = reviewedAt != null;
  const [open, setOpen] = useState(reviewed);
  const [notes, setNotes] = useState(initialNotes ?? "");
  const [mode, setMode] = useState(initialMode ?? "");
  const [pending, startTransition] = useTransition();

  function submit() {
    const fd = new FormData();
    fd.set("verdict_id", String(verdictId));
    fd.set("run_id", String(runId));
    fd.set("trial_id", String(trialId));
    fd.set("reviewer_notes", notes);
    fd.set("failure_mode", mode);
    startTransition(() => {
      void saveVerdictReview(fd);
    });
  }

  return (
    <div className="mt-2 text-xs">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="text-blue-600 hover:underline"
      >
        {reviewed ? `Reviewed${initialMode ? ` · ${initialMode}` : ""}` : "Add note"}
      </button>
      {open && (
        <div className="mt-2 space-y-2 border-l-2 border-zinc-200 dark:border-zinc-700 pl-3">
          <div className="flex items-center gap-2">
            <label className="text-zinc-500">Failure mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 bg-transparent"
            >
              <option value="">(none)</option>
              {FAILURE_MODES.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Why did this verdict fall the way it did?"
            rows={3}
            className="w-full border border-zinc-300 dark:border-zinc-700 rounded p-2 bg-transparent"
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={pending}
              onClick={submit}
              className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
            >
              {pending ? "Saving…" : "Save"}
            </button>
            {reviewedAt && <span className="text-zinc-500">last saved {reviewedAt}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

export function TrialReview({
  trialId,
  runId,
  initialNotes,
}: {
  trialId: number;
  runId: number;
  initialNotes: string | null;
}) {
  const [notes, setNotes] = useState(initialNotes ?? "");
  const [pending, startTransition] = useTransition();

  function submit() {
    const fd = new FormData();
    fd.set("trial_id", String(trialId));
    fd.set("run_id", String(runId));
    fd.set("reviewer_notes", notes);
    startTransition(() => {
      void saveTrialReview(fd);
    });
  }

  return (
    <div className="space-y-2">
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Trial-level notes (observations across criteria)…"
        rows={2}
        className="w-full text-sm border border-zinc-300 dark:border-zinc-700 rounded p-2 bg-transparent"
      />
      <button
        type="button"
        disabled={pending}
        onClick={submit}
        className="text-xs px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
      >
        {pending ? "Saving…" : "Save trial notes"}
      </button>
    </div>
  );
}
