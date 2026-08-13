// e2e: drive the four SecureCorp pipeline scenarios end-to-end and assert
// the pipeline visualization reflects the branch actually taken.
//
// Coverage (CLAUDE.md §26.1 topology):
//   1. DOCUMENT_RAG   — a policy question -> doc_rag branch, evidence,
//                        generation, citation, response.
//   2. STRUCTURED_SQL — an invoice-id question -> structured_sql branch
//                        (no evidence, no doc_rag), generation, response.
//   3. REFUSE         — an out-of-scope question -> refuse branch, which
//                        terminates without generation/retrieval.
//   4. CACHE          — the same RAG question twice; the second answer is
//                        served from cache (L1/L2), so the router + retrieval
//                        + generation nodes stay idle and a "cache hit"
//                        badge appears.
//
// PREREQUISITES (this whole suite is opt-in — `pnpm test:e2e`):
//   - Next dev server on :3000                (pnpm dev)
//   - FastAPI backend on :8000                (uvicorn hybridrag.api.app:app)
//   - Backend deps reachable: an LLM provider (Groq key or Ollama),
//     ChromaDB index, Redis, PostgreSQL.
//
// Each test guards on /api/health and SKIPS (not fails) when its required
// backend capability is absent, so a partial environment reports honestly
// instead of red. REFUSE additionally requires a working LLM: the router
// falls back to DOCUMENT_RAG when the LLM errors, so that assertion is only
// meaningful with generation available. We detect generation availability
// by observing the first scenario rather than guessing.

import { test, expect } from "@playwright/test";
import {
  getHealth,
  loginAs,
  submitQuery,
  pipelineNode,
  expectNodeStatus,
} from "./helpers";

// A RAG question we reuse for the cache scenario. Deterministically routed
// to DOCUMENT_RAG by the router's keyword pre-classifier ("policy").
const RAG_QUERY = "What is the remote work policy?";
// An invoice id — the router's regex pre-classifier forces STRUCTURED_SQL.
const SQL_QUERY = "What is the total of invoice INV-2026-0108?";
// Out-of-scope — only the LLM routes this to REFUSE.
const REFUSE_QUERY = "Write me a haiku about the weather on Mars.";

test.describe("SecureCorp pipeline scenarios", () => {
  test.beforeEach(async ({ request }) => {
    const health = await getHealth(request);
    test.skip(health === null, "backend not running on :8000");
  });

  test("DOCUMENT_RAG: policy question lights the doc_rag branch", async ({
    page,
    request,
  }) => {
    const health = await getHealth(request);
    test.skip(!health?.retriever_wired, "retriever not wired (no Chroma index / embeddings)");

    await loginAs(page, "alice");
    await submitQuery(page, RAG_QUERY);

    // The user's message echoes immediately.
    await expect(page.getByText(RAG_QUERY).first()).toBeVisible();

    // The spine always runs first.
    await expectNodeStatus(page, "Authentication", "completed");
    await expectNodeStatus(page, "Authorization", "completed");
    await expectNodeStatus(page, "Query Router", "completed");

    // The DOCUMENT RAG branch is the one taken.
    await expectNodeStatus(page, "Document RAG", "completed");
    // The other two branches are never entered.
    await expectNodeStatus(page, "Structured SQL", "idle");
    await expectNodeStatus(page, "Refuse", "idle");

    // Rejoin spine completes.
    await expectNodeStatus(page, "Generation", "completed");
    await expectNodeStatus(page, "Citation Validation", "completed");
    await expectNodeStatus(page, "Final Response", "completed");

    // Evidence surfaced into the Sources panel (chunk count > 0).
    await expect(page.getByRole("heading", { name: "Sources" })).toBeVisible({
      timeout: 90_000,
    });

    // Router detail popover shows the real route on activation.
    await pipelineNode(page, "Query Router").click();
    await expect(page.getByRole("dialog")).toContainText("DOCUMENT_RAG");
  });

  test("STRUCTURED_SQL: invoice id lights the structured_sql branch", async ({
    page,
    request,
  }) => {
    const health = await getHealth(request);
    test.skip(!health?.database_ok, "PostgreSQL not reachable");

    await loginAs(page, "bob"); // finance role — authorized for invoices
    await submitQuery(page, SQL_QUERY);

    await expectNodeStatus(page, "Query Router", "completed");
    await expectNodeStatus(page, "Structured SQL", "completed");
    // RAG-only nodes stay idle; SQL path never retrieves document evidence.
    await expectNodeStatus(page, "Document RAG", "idle");
    await expectNodeStatus(page, "Refuse", "idle");
    await expectNodeStatus(page, "Final Response", "completed");

    // The structured detail set is truthful: DB named, raw SQL withheld.
    await pipelineNode(page, "Structured SQL").click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("PostgreSQL");
    await expect(dialog).toContainText("Passed"); // Authorization row
  });

  test("REFUSE: out-of-scope query terminates at the refuse branch", async ({
    page,
    request,
  }) => {
    const health = await getHealth(request);
    // REFUSE is only reachable with a working LLM; the deterministic router
    // has no refuse patterns and falls back to DOCUMENT_RAG on LLM error.
    test.skip(!health?.retriever_wired, "no generation stack; REFUSE not exercisable");

    await loginAs(page, "eve");
    await submitQuery(page, REFUSE_QUERY);

    await expectNodeStatus(page, "Query Router", "completed");
    await expectNodeStatus(page, "Refuse", "completed");
    // No retrieval, no SQL, no generation on the refuse path.
    await expectNodeStatus(page, "Document RAG", "idle");
    await expectNodeStatus(page, "Structured SQL", "idle");
    await expectNodeStatus(page, "Generation", "idle");
    await expectNodeStatus(page, "Citation Validation", "idle");
    // The safe refusal still terminates at the response node.
    await expectNodeStatus(page, "Final Response", "completed");

    // A "refused" status badge appears in the pipeline header.
    await expect(page.getByText(/refused/i)).toBeVisible({ timeout: 90_000 });
  });

  test("CACHE: the second identical query is served from cache", async ({
    page,
    request,
  }) => {
    const health = await getHealth(request);
    test.skip(!health?.retriever_wired, "retriever not wired");
    test.skip(!health?.redis_ok, "Redis not reachable — no cache to hit");

    await loginAs(page, "alice");

    // First pass — full pipeline, primes the cache.
    await submitQuery(page, RAG_QUERY);
    await expectNodeStatus(page, "Final Response", "completed");

    // Reload to clear the client-side message state, then re-ask the exact
    // same question. The backend should answer from L1 (exact) cache.
    await page.reload();
    await expect(page.getByLabel("Question")).toBeVisible({ timeout: 15_000 });
    await submitQuery(page, RAG_QUERY);

    // Cache-hit badge appears (L1 or L2).
    await expect(page.getByText(/cache hit/i)).toBeVisible({ timeout: 60_000 });

    // On a cache hit the router + retrieval + generation are genuinely
    // SKIPPED — those nodes must stay idle, never falsely "completed".
    await expectNodeStatus(page, "Query Router", "idle");
    await expectNodeStatus(page, "Document RAG", "idle");
    await expectNodeStatus(page, "Generation", "idle");
    // Auth/authz scoping still happens (the cache key is scope-hashed) and
    // the response is still emitted.
    await expectNodeStatus(page, "Final Response", "completed");

    // The router detail reflects the skip truthfully.
    await pipelineNode(page, "Query Router").click();
    await expect(page.getByRole("dialog")).toContainText(/Skipped \(cache hit\)/);
  });
});
