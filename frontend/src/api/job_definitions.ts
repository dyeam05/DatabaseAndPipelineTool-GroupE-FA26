import { apiFetch } from "./client";
import {
  type JobDefinitionResponse,
  type JobDefinitionCreate,
  type JobDefinition,
  mapJobDefinition,
} from "./types";

// ─── Job Definitions API ─────────────────────────────────────────────────────

//TODO for vinh: MAKE THIS WORK, this is ai generated. I told it to not do the api



// TODO: Confirm the base path with the backend (e.g. /api/job-definitions)
// TODO: Add pagination support (offset/limit query params) if the backend supports it
// TODO: Add error handling specific to job definition validation errors (422)

/** Fetch all job definitions */
export async function listJobDefinitions(): Promise<JobDefinition[]> {
  const raw = await apiFetch<JobDefinitionResponse[]>("/api/job-definitions");
  return raw.map(mapJobDefinition);
}

/** Fetch a single job definition by ID */
export async function getJobDefinition(id: number): Promise<JobDefinition> {
  const raw = await apiFetch<JobDefinitionResponse>(`/api/job-definitions/${id}`);
  return mapJobDefinition(raw);
}

/** Create a new job definition */
export async function createJobDefinition(
  data: JobDefinitionCreate
): Promise<JobDefinition> {
  const raw = await apiFetch<JobDefinitionResponse>("/api/job-definitions", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return mapJobDefinition(raw);
}

/** Delete a job definition by ID */
// TODO: Confirm DELETE endpoint exists on the backend
export async function deleteJobDefinition(id: number): Promise<void> {
  await apiFetch<void>(`/api/job-definitions/${id}`, { method: "DELETE" });
}

// TODO: Add endpoint to fetch available implementation keys dynamically
//       e.g. GET /api/job-definitions/implementations → string[]
//       This would let the frontend populate a dropdown of registered model
//       implementations instead of requiring free-text input.

// TODO: Add endpoint to fetch available job types dynamically
//       e.g. GET /api/job-definitions/types → string[]
//       This would let the frontend stay in sync with backend-registered types.
