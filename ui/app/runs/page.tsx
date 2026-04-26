import { listRuns } from "@/lib/queries";
import RunsTable from "./runs-table";

export const dynamic = "force-dynamic";

export default function RunsIndex() {
  const runs = listRuns();
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Runs</h1>
        <p className="text-sm text-zinc-500 mt-1">
          All eval runs from the CLI. Click a row for per-case rollup, or select two to compare.
        </p>
      </div>
      <RunsTable
        runs={runs.map((r) => ({
          run_id: r.run_id,
          started_at: r.started_at,
          agent_model: r.agent_model,
          trial_count: r.trial_count,
          mean_correctness: r.mean_correctness,
          total_cost: r.total_cost,
          tag: r.tag,
          config_hash: r.config_hash,
        }))}
      />
    </div>
  );
}
