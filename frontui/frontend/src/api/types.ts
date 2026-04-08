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
  start_seconds?: number;
  duration_seconds?: number;
  frame_count?: number;
  // Annotation counts — present when status is annotated/reviewed
  annotation_person?: number;
  annotation_bicycle?: number;
  annotation_car?: number;
  annotation_motorbike?: number;
  annotation_bus?: number;
  annotation_train?: number;
  annotation_truck?: number;
  annotation_traffic_light?: number;
  annotation_stop_sign?: number;
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
  return {
    index: s.segment_id,
    routeId: s.route_id,
    startSeconds: s.start_seconds ?? 0,
    durationSeconds: s.duration_seconds ?? 0,
    frameCount: s.frame_count ?? 0,
    status: s.status,
    annotations: {
      person:       s.annotation_person       ?? 0,
      bicycle:      s.annotation_bicycle      ?? 0,
      car:          s.annotation_car          ?? 0,
      motorbike:    s.annotation_motorbike    ?? 0,
      bus:          s.annotation_bus          ?? 0,
      train:        s.annotation_train        ?? 0,
      truck:        s.annotation_truck        ?? 0,
      trafficLight: s.annotation_traffic_light ?? 0,
      stopSign:     s.annotation_stop_sign    ?? 0,
    },
  };
}
