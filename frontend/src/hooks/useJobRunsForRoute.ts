import { useQuery } from "@tanstack/react-query";
import { listJobRunsForRoute } from "../api/job_runs";
import { JOB_TERMINAL_STATUSES } from "../api/types";

/**
 * Polls job runs for a given route.
 *
 * - Polls every 3 s while any job run is queued or running.
 * - Polls every 5 s when there are no runs yet (in case one gets created).
 * - Stops polling once all existing runs reach a terminal state
 *   (succeeded | failed | cancelled).
 *
 * A route has an annotation "in progress" when this query returns at least
 * one run whose status is "queued" or "running".
 */
export function useJobRunsForRoute(routeId?: string) {
  return useQuery({
    queryKey: ["jobRuns", routeId],
    queryFn: () => {
      if (!routeId) throw new Error("Missing routeId");
      return listJobRunsForRoute(routeId);
    },
    enabled: !!routeId,
    refetchInterval: (query) => {
      const runs = query.state.data;

      // No data yet — keep checking
      if (!runs || runs.length === 0) return 5000;

      const allDone = runs.every((r) => JOB_TERMINAL_STATUSES.includes(r.status));
      return allDone ? false : 3000;
    },
  });
}

/** Returns true if any job run for the route is still queued or running. */
export function isAnnotationInProgress(
  runs: ReturnType<typeof useJobRunsForRoute>["data"]
): boolean {
  if (!runs || runs.length === 0) return false;
  return runs.some((r) => r.status === "queued" || r.status === "running");
}
