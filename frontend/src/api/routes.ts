import { apiFetch, API_BASE } from "./client";
import { mapRoute } from "./types";
import type { Route, RouteResponse } from "./types";

export async function listRoutes(): Promise<Route[]> {
  const data = await apiFetch<RouteResponse[]>("/routes/");
  return data.map(mapRoute);
}

export async function getRoute(routeId: string): Promise<Route> {
  const data = await apiFetch<RouteResponse>(`/routes/${encodeURIComponent(routeId)}`);
  return mapRoute(data);
}

export async function createRoute(routeId: string): Promise<Route> {
  const data = await apiFetch<RouteResponse>("/routes/", {
    method: "POST",
    body: JSON.stringify({ route_id: routeId }),
  });
  return mapRoute(data);
}

export async function deleteRoute(routeId: string): Promise<void> {
  await apiFetch<void>(`/routes/${encodeURIComponent(routeId)}`, { method: "DELETE" });
}

/**
 * Returns the URL for the thumbnail of a given segment.
 * The backend must expose GET /segments/{route_id}/{segment_id}/thumbnail
 * returning either an image or a redirect to a MinIO presigned URL.
 * Falls back to an empty string (the <img> onError handler will show a placeholder).
 */
export function getThumbnailUrl(routeId: string, segmentId: number): string {
  return `${API_BASE}/segments/${encodeURIComponent(routeId)}/${segmentId}/thumbnail`;
}