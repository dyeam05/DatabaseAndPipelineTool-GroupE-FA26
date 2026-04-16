import { apiFetch, ApiError } from "./client";
import {
  type JobDefinitionResponse,
  type JobDefinitionCreate,
  type JobDefinition,
  mapJobDefinition,
} from "./types";

// ─── Job Definitions API ─────────────────────────────────────────────────────


// TODO: Confirm the base path with the backend (e.g. /job-definitions)
// TODO: Add pagination support (offset/limit query params) if the backend supports it. back end currently does not support pagination
// TODO: Add error handling specific to job definition validation errors (422)

/** Fetch all job definitions */
export async function listJobDefinitions(): Promise<JobDefinition[]> {
  const raw = await apiFetch<JobDefinitionResponse[]>("/job-definitions/");
  return raw.map(mapJobDefinition);
}

/** Fetch a single job definition by ID */
export async function getJobDefinition(id: number): Promise<JobDefinition> {
  const raw = await apiFetch<JobDefinitionResponse>(`/job-definitions/${id}`);
  return mapJobDefinition(raw);
}

/** Create a new job definition */
export async function createJobDefinition(
  data: JobDefinitionCreate
): Promise<JobDefinition> {
  try {
    const raw = await apiFetch<JobDefinitionResponse>("/job-definitions/", {
      method: "POST",
      body: JSON.stringify({
        type: data.type,
        implementation_key: data.implementation_key,
        name: data.name,
        config: data.config,
        description: data.description,
      }),
    });
    return mapJobDefinition(raw);
  } catch (err) {
    // 422 error
    if (err instanceof ApiError && err.status === 422) {
      throw new Error(`Validation error: ${err.message}`);
    }
    throw err;
  }
}

/** Delete a job definition by ID */
// TODO: Confirm DELETE endpoint exists on the backend
export async function deleteJobDefinition(id: number): Promise<void> {
  await apiFetch<void>(`/job-definitions/${id}`, { method: "DELETE" });
}

// TODO: Add endpoint to fetch available implementation keys dynamically
//       e.g. GET /job-definitions/implementations → string[]
//       This would let the frontend populate a dropdown of registered model
//       implementations instead of requiring free-text input.
export async function listImplementationKeys(): Promise<string[]> {
  return apiFetch<string[]>("/job-definitions/implementations");
}

// TODO: Add endpoint to fetch available job types dynamically
//       e.g. GET /job-definitions/types → string[]
//       This would let the frontend stay in sync with backend-registered types.
export async function listJobTypes(): Promise<string[]> {
  return apiFetch<string[]>("/job-definitions/types");
}