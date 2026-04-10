// ─── API Response Types ───────────────────────────────────────────────────────
// These mirror the Pydantic schemas returned by the FastAPI backend.
// Field names are snake_case to match what FastAPI serialises by default.
// Adjust here if your schemas differ.

export type RouteStatus =
  | "download_queue"
  | "downloading"
  | "download_failed"
  | "downloaded"
  | "segmented"
  | "annotating"
  | "annotated"
  | "reviewed"
  | "failed";

export type SegmentStatus =
  | "recorded"
  | "annotating"
  | "annotated"
  | "reviewed"
  | "failed";

/** Mirrors RouteResponse from shared/schemas/route.py */
export interface RouteResponse {
  route_id: string;
  status: RouteStatus;
  vehicle_id?: string;
  recorded_at?: string;        // ISO-8601 string
  duration_seconds?: number;
  segment_count?: number;
  annotated_segment_count?: number;
  annotating_segment_count?: number;
  failed_segment_count?: number;
}

/** Mirrors SegmentResponse from shared/schemas/segment.py */
export interface SegmentResponse {
  route_id: string;
  segment_id: number;
  status: SegmentStatus;

  start_time: string;
  end_time: string;

  frame_count?: number;
}

// ─── Normalised frontend types ────────────────────────────────────────────────
// Camel-case versions used throughout the UI.

export type AnnotationStatus =
  | "recorded"
  | "segmented"
  | "annotating"
  | "annotated"
  | "reviewed"
  | "failed"
  | "downloading"
  | "downloaded"
  | "download_queue"
  | "download_failed";

export interface Route {
  id: string;
  vehicleId: string;
  recordedAt: string;
  durationSeconds: number;
  segmentCount: number;
  annotatedSegmentCount: number;
  annotatingSegmentCount: number;
  failedSegmentCount: number;
  status: AnnotationStatus;
}

export interface Segment {
  index: number;
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

// ─── Mappers ──────────────────────────────────────────────────────────────────

export function mapRoute(r: RouteResponse): Route {
  return {
    id: r.route_id,
    vehicleId: r.vehicle_id ?? "unknown",
    recordedAt: r.recorded_at ?? new Date(0).toISOString(),
    durationSeconds: r.duration_seconds ?? 0,
    segmentCount: r.segment_count ?? 0,
    annotatedSegmentCount: r.annotated_segment_count ?? 0,
    annotatingSegmentCount: r.annotating_segment_count ?? 0,
    failedSegmentCount: r.failed_segment_count ?? 0,
    status: r.status as AnnotationStatus,
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
    routeId: s.route_id,

    // TEMP: will fix startSeconds next step
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
