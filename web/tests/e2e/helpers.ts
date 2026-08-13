// Shared helpers for the opt-in e2e suite.
//
// These are NOT a test file (no `.spec.` in the name), so Playwright does
// not collect them — but tsc still typechecks them via the web tsconfig.

import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface Health {
  status: string;
  retriever_wired: boolean;
  redis_ok: boolean;
  database_ok: boolean;
}

/** Fetch /api/health, or null if the backend is unreachable. */
export async function getHealth(request: APIRequestContext): Promise<Health | null> {
  try {
    const res = await request.get(`${API_BASE}/api/health`, { timeout: 3_000 });
    if (!res.ok()) return null;
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

/** Sign in via the credentials form (email prefix -> user_id) and land on
 *  the dashboard, then navigate to the chat surface. */
export async function loginAs(page: Page, userId: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel(/Work email/i).fill(`${userId}@nexacore.com`);
  await page.getByRole("button", { name: /^Sign In$/ }).click();
  await page.waitForURL(/\/dashboard$/, { timeout: 15_000 });
  await page.goto("/chat");
  // The chat gate resolves /api/auth/me before rendering the input.
  await expect(page.getByLabel("Question")).toBeVisible({ timeout: 15_000 });
}

/** Type a query into the chat box and press Send. */
export async function submitQuery(page: Page, query: string): Promise<void> {
  await page.getByLabel("Question").fill(query);
  await page.getByRole("button", { name: /^Send$/ }).click();
}

/** Locate a pipeline node button by its label.
 *
 *  Matches on the accessible name, whose format is `${label} — ${status}`.
 *  We anchor on `^${label} ` (label + the space that always precedes the
 *  " — status" suffix) rather than filtering by visible text: the Query
 *  Router node's sub-label lists "RAG · SQL · Refuse", which would collide
 *  with a hasText("Refuse") match, and anchoring avoids depending on the
 *  exact dash codepoint. `data-status` on the returned button is the
 *  ground-truth state from the pure reducer. */
export function pipelineNode(page: Page, label: string) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return page.getByRole("button", { name: new RegExp(`^${escaped} `) });
}

/** Assert a node settles into the given status (auto-retries to timeout). */
export async function expectNodeStatus(
  page: Page,
  label: string,
  status: "idle" | "processing" | "completed" | "failed",
  timeout = 90_000,
): Promise<void> {
  await expect(pipelineNode(page, label)).toHaveAttribute("data-status", status, { timeout });
}
