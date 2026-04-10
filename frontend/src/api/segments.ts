import { apiFetch } from "./client";
import type { SegmentResponse, Segment } from "./types";
import { mapSegment } from "./types";

export async function listSegments(): Promise<Segment[]> {
  const data = await apiFetch<SegmentResponse[]>("/segments/");
  return data.map(mapSegment);
}

/**
 * Returns all segments for a given route by fetching all segments and
 * filtering client-side.  If your backend gains a ?route_id= query param
 * in the future, update this function to use it instead.
 */
export async function listSegmentsForRoute(routeId: string): Promise<Segment[]> {
  const raw = await apiFetch<SegmentResponse[]>("/segments/");

  const filtered = raw
    .filter((s) => s.route_id === routeId)
    .sort((a, b) => a.segment_id - b.segment_id);

  if (filtered.length === 0) return [];

  const baseTime = new Date(filtered[0].start_time).getTime();

  return filtered.map((s) => {
    const start = new Date(s.start_time).getTime();
    const end = new Date(s.end_time).getTime();

    return {
      index: s.segment_id,
      routeId: s.route_id,
      startSeconds: Math.floor((start - baseTime) / 1000),
      durationSeconds: Math.floor((end - start) / 1000),
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
  });
}

export async function getSegment(routeId: string, segmentId: number): Promise<Segment> {
  const data = await apiFetch<SegmentResponse>(
    `/segments/${encodeURIComponent(routeId)}/${segmentId}`
  );
  return mapSegment(data);
}

export async function deleteSegment(routeId: string, segmentId: number): Promise<void> {
  await apiFetch<void>(
    `/segments/${encodeURIComponent(routeId)}/${segmentId}`,
    { method: "DELETE" }
  );
}
