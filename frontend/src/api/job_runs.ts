import { apiFetch } from "./client";
import { mapJobRun } from "./types";
import type { JobRun, JobRunResponse } from "./types";

export async function listJobRuns(): Promise<JobRun[]> {
  const data = await apiFetch<JobRunResponse[]>("/job-runs/");
  return data.map(mapJobRun);
}

/**
 * Returns all job runs for a given route by fetching all job runs and
 * filtering client-side. If the backend gains a ?route_id= query param,
 * update this to use it.
 */
export async function listJobRunsForRoute(routeId: string): Promise<JobRun[]> {
  const all = await apiFetch<JobRunResponse[]>("/job-runs/");
  return all
    .filter((j) => j.route_id === routeId)
    .map(mapJobRun);
}
