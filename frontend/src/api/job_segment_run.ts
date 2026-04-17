import { apiFetch } from "./client";
import { mapCvatImport, mapJobSegmentRun } from "./types";
import type { CvatImport, CvatImportResponse, JobSegmentRun, JobSegmentRunResponse } from "./types";

export async function getCvatImportForRun(params: {
  routeId: string;
  jobDefId: number;
  jobRunNum: number;
  segmentId: number;
  camera: string;
}): Promise<CvatImport | null> {
  const qs = new URLSearchParams({
    route_id: params.routeId,
    job_def_id: String(params.jobDefId),
    job_run_num: String(params.jobRunNum),
    segment_id: String(params.segmentId),
    camera: params.camera,
  });
  const data = await apiFetch<CvatImportResponse | null>(
    `/job_segment_run/cvat-import?${qs}`
  );
  return data ? mapCvatImport(data) : null;
}


export async function getJobSegmentRunsForSegment(routeId: string, segmentId: number): Promise<JobSegmentRun[]> {
  const data = await apiFetch<JobSegmentRunResponse[]>(
    `/job_segment_run/${encodeURIComponent(routeId)}/${encodeURIComponent(segmentId)}`
  );
  return data.map(mapJobSegmentRun);
}


export async function importToCvat(params: {
  routeId: string;
  jobDefId: number;
  jobRunNum: number;
  segmentId: number;
  camera: string;
}): Promise<CvatImport> {
  const qs = new URLSearchParams({
    route_id: params.routeId,
    job_def_id: String(params.jobDefId),
    job_run_num: String(params.jobRunNum),
    segment_id: String(params.segmentId),
    camera: params.camera,
  });
  const data = await apiFetch<CvatImportResponse>(
    `/job_segment_run/cvat-import?${qs}`,
    { method: "POST" }
  );
  return mapCvatImport(data);
}
