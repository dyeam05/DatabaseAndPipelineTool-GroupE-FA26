import { apiFetch } from "./client";

interface RestartCvatResponse {
  status: string;
  elapsed_seconds: number;
}

export async function restartCvat(): Promise<RestartCvatResponse> {
  return apiFetch<RestartCvatResponse>("/cvat/restart", { method: "POST" });
}
