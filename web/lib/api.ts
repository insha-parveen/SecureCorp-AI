// Typed fetch wrappers for the FastAPI surface.
//
// All requests are credentialed (httpOnly cookie carries the JWT). The
// frontend never reads the token — it only knows whether the call
// succeeded or returned 401.

import type { User } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

class HttpError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "HttpError";
  }
}

async function jsonFetch<T>(
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.json !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
    credentials: "include", // send the httpOnly cookie
    body: init?.json !== undefined ? JSON.stringify(init.json) : init?.body,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body; status text is enough */
    }
    throw new HttpError(response.status, detail);
  }
  return (await response.json()) as T;
}

export function listDemoUsers(): Promise<{ users: User[] }> {
  return jsonFetch<{ users: User[] }>("/api/auth/users");
}

export function login(userId: string): Promise<User> {
  return jsonFetch<User>("/api/auth/token", { method: "POST", json: { user_id: userId } });
}

export function logout(): Promise<{ ok: true }> {
  return jsonFetch<{ ok: true }>("/api/auth/logout", { method: "POST" });
}

export function me(): Promise<User> {
  return jsonFetch<User>("/api/auth/me");
}

export interface AnalyticsOverview {
  total_queries: number;
  avg_latency: number;
  cache_hit_rate: number;
  refusal_rate: number;
}

export interface ChartPointDTO {
  label: string;
  value: number;
}

export interface QueryTypeDTO {
  label: string;
  value: number;
  color: string;
}

export function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return jsonFetch<AnalyticsOverview>("/api/analytics/overview");
}

export function getQueriesOverTime(): Promise<ChartPointDTO[]> {
  return jsonFetch<ChartPointDTO[]>("/api/analytics/queries-over-time");
}

export function getQueryTypes(): Promise<QueryTypeDTO[]> {
  return jsonFetch<QueryTypeDTO[]>("/api/analytics/query-types");
}

export { HttpError };
