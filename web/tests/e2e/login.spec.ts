// e2e: the rebuilt /login glass card, and a full demo-login round trip.
//
// Two tiers:
//   1. "glass card layout" — pure frontend render. Needs ONLY the Next
//      dev server (no backend): the credentials view does not fetch.
//   2. "demo login round trip" — needs the FastAPI backend on :8000 to
//      issue the JWT cookie. Skipped automatically when the backend is
//      down so the suite stays green in a frontend-only checkout.
//
// This whole suite is opt-in (run with `pnpm test:e2e`); the unit gate
// (`pnpm test` / vitest) never touches tests/e2e.

import { test, expect, type APIRequestContext } from "@playwright/test";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function backendUp(request: APIRequestContext): Promise<boolean> {
  try {
    const res = await request.get(`${API_BASE}/api/health`, { timeout: 3_000 });
    return res.ok();
  } catch {
    return false;
  }
}

test.describe("login glass card", () => {
  test("renders the rebuilt glass card (no backend required)", async ({ page }) => {
    await page.goto("/login");

    // Wordmark + kicker above the card.
    await expect(page.getByRole("heading", { name: "SecureCorp AI" })).toBeVisible();

    // The credentials form: work email + password + primary CTA.
    await expect(page.getByLabel(/Work email/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /^Sign In$/ })).toBeVisible();

    // Trust footer from the reference image.
    await expect(page.getByText(/Protected by enterprise-grade security/i)).toBeVisible();

    // The demo-account disclosure is reachable (MVP auth path).
    await expect(
      page.getByRole("button", { name: /Sign in with a demo account/i }),
    ).toBeVisible();
  });

  test("demo picker lists seeded users", async ({ page, request }) => {
    test.skip(!(await backendUp(request)), "backend not running on :8000");

    await page.goto("/login");
    await page.getByRole("button", { name: /Sign in with a demo account/i }).click();

    // The picker fetches /api/auth/users; alice (hr) is always seeded.
    await expect(page.getByText("alice")).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("login round trip", () => {
  test("credentials form signs in and lands on the dashboard", async ({ page, request }) => {
    test.skip(!(await backendUp(request)), "backend not running on :8000");

    await page.goto("/login");
    // The email prefix becomes the user_id (alice@… -> "alice").
    await page.getByLabel(/Work email/i).fill("alice@nexacore.com");
    await page.getByRole("button", { name: /^Sign In$/ }).click();

    await page.waitForURL(/\/dashboard$/, { timeout: 15_000 });
  });
});
