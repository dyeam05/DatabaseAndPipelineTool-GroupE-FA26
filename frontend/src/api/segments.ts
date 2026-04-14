  import { apiFetch } from "./client";
  import type { SegmentResponse, Segment } from "./types";
  import { mapSegment } from "./types";

  export async function listSegments(): Promise<Segment[]> {
    const data = await apiFetch<SegmentResponse[]>("/segments/");
    return data.map(mapSegment);
  }

  export async function listSegmentsForRoute(routeId: string): Promise<Segment[]> {
    const raw = await apiFetch<SegmentResponse[]>(`/segments/by-route/${encodeURIComponent(routeId)}`);

    if (raw.length === 0) return [];

    const baseTime = new Date(raw[0].start_time).getTime();

    return raw.map((s) => ({
      ...mapSegment(s),
      startSeconds: Math.floor((new Date(s.start_time).getTime() - baseTime) / 1000),
    }));
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
