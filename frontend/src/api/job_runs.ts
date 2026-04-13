import { apiFetch } from "./client";
import { mapJobRun } from "./types";
import type { JobRun, JobRunResponse } from "./types";

export async function listJobRuns(): Promise<JobRun[]> {
  const data = await apiFetch<JobRunResponse[]>("/job-runs/");
  return data.map(mapJobRun);
}

export async function listJobRunsForRoute(routeId: string): Promise<JobRun[]> {
  const data = await apiFetch<JobRunResponse[]>(`/job-runs/by-route/${routeId}`);
  return data.map(mapJobRun);
}
