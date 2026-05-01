import { apiFetch } from "./client";

interface RestartCvatResponse {
  status: string;
  elapsed_seconds: number;
}

interface CvatActiveStatusResponse {
  active: boolean;
}

export async function restartCvat(): Promise<RestartCvatResponse> {
  return apiFetch<RestartCvatResponse>("/cvat/restart", { method: "POST" });
}

export async function getCvatActiveStatus(): Promise<CvatActiveStatusResponse> {
  return apiFetch<CvatActiveStatusResponse>("/cvat/active-status");
}
