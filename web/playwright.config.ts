// Playwright config — runs the e2e suite against the local dev server.
// The tests themselves live in `tests/e2e/*.spec.ts`.

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  // The tests assume the dev server is running. We don't auto-start it
  // here so the user keeps control of the dev environment.
});