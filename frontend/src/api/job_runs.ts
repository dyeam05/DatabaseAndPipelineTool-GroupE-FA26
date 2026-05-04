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

export async function createJobRun(params: {
  jobDefId: number;
  routeId: string;
  camera: string;
}): Promise<JobRun> {
  const data = await apiFetch<JobRunResponse>("/job-runs/", {
    method: "POST",
    body: JSON.stringify({
      job_def_id: params.jobDefId,
      route_id: params.routeId,
      camera: params.camera,
    }),
  });
  return mapJobRun(data);
}

export async function deleteJobRun(params: {
  jobDefId: number;
  jobRunNum: number;
  routeId: string;
  camera: string;
}): Promise<void> {
  const qs = new URLSearchParams({
    job_def_id: String(params.jobDefId),
    job_run_num: String(params.jobRunNum),
    route_id: params.routeId,
    camera: params.camera,
  });
  await apiFetch<void>(`/job-runs/?${qs}`, { method: "DELETE" });
}

export async function cancelJobRun(params: {
  jobDefId: number;
  jobRunNum: number;
  routeId: string;
  camera: string;
}): Promise<JobRun> {
  const qs = new URLSearchParams({
    job_def_id: String(params.jobDefId),
    job_run_num: String(params.jobRunNum),
    route_id: params.routeId,
    camera: params.camera,
  });
  const data = await apiFetch<JobRunResponse>(`/job-runs/cancel?${qs}`, { method: "POST" });
  return mapJobRun(data);
}

export async function requeueJobRun(params: {
  jobDefId: number;
  jobRunNum: number;
  routeId: string;
  camera: string;
}): Promise<JobRun> {
  const qs = new URLSearchParams({
    job_def_id: String(params.jobDefId),
    job_run_num: String(params.jobRunNum),
    route_id: params.routeId,
    camera: params.camera,
  });
  const data = await apiFetch<JobRunResponse>(`/job-runs/requeue?${qs}`, { method: "POST" });
  return mapJobRun(data);
}
