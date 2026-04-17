// ─── API Response Types ───────────────────────────────────────────────────────
// These mirror the Pydantic schemas returned by the FastAPI backend.
// Field names are snake_case to match what FastAPI serialises by default.
// Adjust here if your schemas differ.

export type RouteStatus =
  | "download queue"
  | "downloading"
  | "upload queue"
  | "uploading"
  | "failed"
  | "uploaded";

export type SegmentStatus =
  | "download queue"
  | "downloading"
  | "upload queue"
  | "uploading"
  | "failed"
  | "uploaded";

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

/** Terminal states — polling stops when a resource reaches one of these */
export const ROUTE_TERMINAL_STATUSES: RouteStatus[] = ["uploaded", "failed"];
export const SEGMENT_TERMINAL_STATUSES: SegmentStatus[] = ["uploaded", "failed"];
export const JOB_TERMINAL_STATUSES: JobStatus[] = ["succeeded", "failed", "cancelled"];

export interface RouteResponse {
  route_id: string;
  file_path: string | null;
  status: RouteStatus;
  created_at: string;
}

export interface SegmentResponse {
  route_id: string;
  segment_id: number;
  status: SegmentStatus;
  start_time: string;
  end_time: string;
  created_at: string;
  frame_count?: number;
}

export interface JobRunResponse {
  job_run_num: number;
  job_def_id: number;
  route_id: string;
  status: JobStatus;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  stats: Record<string, unknown> | null;
}

// ─── Normalised frontend types ────────────────────────────────────────────────
// Camel-case versions used throughout the UI.

export interface Route {
  id: string;
  filePath: string | null;
  createdAt: string;
  status: RouteStatus;
}

export interface Segment {
  index: number;
  segmentId: number;
  routeId: string;
  startSeconds: number;
  durationSeconds: number;
  frameCount: number;
  status: SegmentStatus;
  annotations: {
    person: number;
    bicycle: number;
    car: number;
    motorbike: number;
    bus: number;
    train: number;
    truck: number;
    trafficLight: number;
    stopSign: number;
  };
}

export interface JobRun {
  jobRunNum: number;
  jobDefId: number;
  routeId: string;
  status: JobStatus;
  queuedAt: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  error: string | null;
  stats: Record<string, unknown> | null;
}

// ─── Job Definition Types ────────────────────────────────────────────────────

export type JobType = "object_detection" | "lane_detection" | "segmentation";

export interface JobDefinitionResponse {
  job_def_id: number;
  type: JobType;
  implementation_key: string;
  name: string;
  config: Record<string, unknown>;
  description: string;
  created_at: string;
}

export interface JobDefinitionCreate {
  type: JobType;
  implementation_key: string;
  name: string;
  config: Record<string, unknown>;
  description: string;
}

export interface JobDefinition {
  id: number;
  type: JobType;
  implementationKey: string;
  name: string;
  config: Record<string, unknown>;
  description: string;
  createdAt: string;
}

// ─── Mappers ──────────────────────────────────────────────────────────────────

export function mapRoute(r: RouteResponse): Route {
  return {
    id: r.route_id,
    filePath: r.file_path,
    createdAt: r.created_at,
    status: r.status,
  };
}

export function mapSegment(s: SegmentResponse): Segment {
  const start = new Date(s.start_time);
  const end = new Date(s.end_time);

  const durationSeconds = Math.max(
    0,
    (end.getTime() - start.getTime()) / 1000
  );

  return {
    index: s.segment_id,
    segmentId: s.segment_id,
    routeId: s.route_id,

    // startSeconds is calculated relative to first segment in listSegmentsForRoute
    startSeconds: 0,

    durationSeconds,
    frameCount: s.frame_count ?? 0,
    status: s.status,

    annotations: {
      person: 0,
      bicycle: 0,
      car: 0,
      motorbike: 0,
      bus: 0,
      train: 0,
      truck: 0,
      trafficLight: 0,
      stopSign: 0,
    },
  };
}

export function mapJobRun(j: JobRunResponse): JobRun {
  return {
    jobRunNum: j.job_run_num,
    jobDefId: j.job_def_id,
    routeId: j.route_id,
    status: j.status,
    queuedAt: j.queued_at,
    startedAt: j.started_at,
    finishedAt: j.finished_at,
    error: j.error,
    stats: j.stats,
  };
}

export function mapJobDefinition(j: JobDefinitionResponse): JobDefinition {
  return {
    id: j.job_def_id,
    type: j.type,
    implementationKey: j.implementation_key,
    name: j.name,
    config: j.config,
    description: j.description,
    createdAt: j.created_at,
  };
}
