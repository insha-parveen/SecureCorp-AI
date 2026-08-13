// Unit tests for the landing page's data + signature component.
//
// The most important test here is the HONESTY GUARD: CLAUDE.md §20/§24.5
// forbid inventing benchmark values (RAGAS scores, latency, cache-hit rate).
// landing-facts.ts is the single source of every number the page renders, so
// we assert mechanically that (a) the forbidden metrics never appear and
// (b) the BM25 probe keeps its "diagnostic, not a benchmark" caveat. If a
// future edit sneaks a fabricated metric onto the page through this module,
// this test fails.

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  BM25_PROBE,
  CORPUS_STATS,
  EXAMPLE_TRACE,
  RETRIEVAL_CONFIG,
  ROLES,
  SOURCE_BREAKDOWN,
} from "@/lib/landing-facts";
import { TraceCard } from "@/components/landing/trace-card";

describe("landing-facts honesty guard", () => {
  it("carries a source on every corpus stat", () => {
    for (const stat of CORPUS_STATS) {
      expect(stat.source.length).toBeGreaterThan(0);
    }
  });

  it("labels the BM25 result a diagnostic probe, not a benchmark", () => {
    expect(BM25_PROBE.caveat.toLowerCase()).toContain("diagnostic probe");
    expect(BM25_PROBE.caveat.toLowerCase()).toContain("not the phase 8");
    // The real measured values from §7.
    expect(BM25_PROBE.bm25HitAt1).toBe(40);
    expect(BM25_PROBE.denseHitAt1).toBe(4);
    expect(BM25_PROBE.identifiers).toBe(40);
  });

  it("does not smuggle in unmeasured metrics (RAGAS / latency / cache-hit rate)", () => {
    // Serialize the entire fact surface and scan for the forbidden vocabulary.
    // These have no real measurement yet, so they must not appear anywhere.
    const blob = JSON.stringify({
      CORPUS_STATS,
      SOURCE_BREAKDOWN,
      RETRIEVAL_CONFIG,
      BM25_PROBE,
      EXAMPLE_TRACE,
    }).toLowerCase();
    for (const forbidden of ["ragas", "faithfulness", "latency", "p95", "hit rate", "hit-rate"]) {
      expect(blob).not.toContain(forbidden);
    }
  });

  it("keeps the source breakdown consistent with the six roles", () => {
    expect(ROLES).toHaveLength(6);
    // Every breakdown row is a positive count — no zero-padding placeholders.
    for (const row of SOURCE_BREAKDOWN) {
      expect(row.docs).toBeGreaterThan(0);
      expect(row.chunks).toBeGreaterThan(0);
    }
  });
});

describe("TraceCard", () => {
  it("renders the prompt, aligned key = value rows, and footer", () => {
    render(
      <TraceCard
        label="example request"
        prompt="What is the remote work policy?"
        lines={[
          { key: "route", value: "DOCUMENT_RAG", tone: "route-rag" },
          { key: "authz", value: "PASS", tone: "pass", ok: true },
        ]}
        footer="Observed e2e run"
      />,
    );
    expect(screen.getByText("What is the remote work policy?")).toBeTruthy();
    expect(screen.getByText("route")).toBeTruthy();
    expect(screen.getByText("DOCUMENT_RAG")).toBeTruthy();
    expect(screen.getByText("authz")).toBeTruthy();
    expect(screen.getByText("Observed e2e run")).toBeTruthy();
  });

  it("renders without a prompt or footer", () => {
    const { container } = render(
      <TraceCard label="minimal" lines={[{ key: "k", value: "v" }]} />,
    );
    expect(container).toBeTruthy();
    expect(screen.getByText("minimal")).toBeTruthy();
  });
});
