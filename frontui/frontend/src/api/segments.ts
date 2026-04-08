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
  const all = await listSegments();
  return all.filter((s) => s.routeId === routeId).sort((a, b) => a.index - b.index);
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
