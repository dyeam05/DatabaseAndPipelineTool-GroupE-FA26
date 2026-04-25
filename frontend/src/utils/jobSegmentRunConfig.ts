import type { CvatImport, JobSegmentRun, JobSegmentRunStatus } from "../api/types";

export const STATUS_COLOR: Record<JobSegmentRunStatus, string> = {
  queued:    "var(--text-secondary)",
  running:   "var(--accent-caution)",
  succeeded: "var(--accent-go)",
  failed:    "var(--accent-alert)",
  cancelled: "var(--text-muted)",
};

export const STATUS_LABEL: Record<JobSegmentRunStatus, string> = {
  queued: "Queued", running: "Running", succeeded: "Succeeded", failed: "Failed", cancelled: "Cancelled",
};

export type CvatActionState = "unavailable" | "load" | "in_progress" | "open";
export interface CvatAction { state: CvatActionState; label: string; }

export function resolveAction(run: JobSegmentRun, imp: CvatImport | null, isPending: boolean): CvatAction {
  if (isPending)                  return { state: "in_progress", label: "Loading…" };
  if (run.status !== "succeeded") return { state: "unavailable", label: "Not Available" };
  if (!imp || imp.status === "removed" || imp.status === "failed")
                                  return { state: "load",        label: "Load into CVAT" };
  if (imp.status === "loaded")    return { state: "open",        label: "Open in CVAT ↗" };
  return                                 { state: "in_progress", label: "In Progress" };
}
