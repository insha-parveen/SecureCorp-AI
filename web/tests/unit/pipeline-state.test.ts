// Unit tests for the pure pipeline-state reducer. These lock the
// truthfulness contract (CLAUDE.md §26.3): only the branch actually taken
// is ever lit, cache hits never imply retrieval, and errors surface on the
// node that was in flight.

import { describe, expect, it } from "vitest";
import {
  derivePipelineState,
  messageFromEvents,
  pipelineStateFromEvents,
  PIPELINE_NODE_IDS,
  type NodeStatus,
  type PipelineNodeId,
} from "@/lib/pipeline-state";
import type { ChatEvent, DonePayload, RankedEvidence } from "@/lib/types";

const EV1: RankedEvidence = {
  rank: 1,
  chunk_id: "HR-001:v1:0001",
  document_id: "HR-001",
  document_title: "HR-001",
  section_title: null,
  excerpt: "Remote work policy…",
};

function done(data: Partial<DonePayload> = {}): ChatEvent {
  return {
    event: "done",
    data: {
      answer: "answer",
      citations: [1],
      evidence: [EV1],
      model: "llama-3.1-8b-instant",
      usage: {},
      extras: {},
      ...data,
    },
  };
}

function statusesOf(ids: PipelineNodeId[], s: Record<PipelineNodeId, NodeStatus>) {
  return ids.map((id) => s[id]);
}

describe("derivePipelineState — no request yet", () => {
  it("is all idle before submit", () => {
    const state = derivePipelineState(null, false);
    expect(state.activeNodeId).toBeNull();
    expect(state.route).toBeNull();
    expect(state.cacheHit).toBe(false);
    for (const id of PIPELINE_NODE_IDS) expect(state.statuses[id]).toBe("idle");
  });
});

describe("DOCUMENT_RAG branch", () => {
  it("pre-meta (in-flight, no meta yet): SQL + refuse + doc_rag stay idle", () => {
    // A streaming request that has emitted nothing but an (empty) token —
    // we know only that auth/authz/routing are in flight.
    const msg = messageFromEvents([{ event: "token", data: { text: "" } }]);
    const s = derivePipelineState(msg, true);
    expect(s.route).toBeNull();
    expect(s.activeNodeId).toBe("auth");
    expect(s.statuses.structured_sql).toBe("idle");
    expect(s.statuses.refuse).toBe("idle");
    expect(s.statuses.doc_rag).toBe("idle");
  });

  it("lights the RAG branch and leaves SQL + REFUSE idle", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "DOCUMENT_RAG", cache_tier: "MISS" } },
      { event: "evidence", data: EV1 },
      { event: "token", data: { text: "The policy " } },
    ];
    const s = pipelineStateFromEvents(events);
    expect(s.route).toBe("DOCUMENT_RAG");
    // Off-branch nodes never light for a RAG query.
    expect(s.statuses.structured_sql).toBe("idle");
    expect(s.statuses.refuse).toBe("idle");
    // doc_rag completed once tokens flow; generation is the active node.
    expect(s.statuses.doc_rag).toBe("completed");
    expect(s.activeNodeId).toBe("generation");
  });

  it("marks the full RAG path completed on done", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "DOCUMENT_RAG", cache_tier: "MISS" } },
      { event: "evidence", data: EV1 },
      { event: "token", data: { text: "answer" } },
      done(),
    ];
    const s = pipelineStateFromEvents(events, false);
    expect(statusesOf(["user", "auth", "authz", "router", "doc_rag", "generation", "citation", "response"], s.statuses)).toEqual(
      ["completed", "completed", "completed", "completed", "completed", "completed", "completed", "completed"],
    );
    expect(s.statuses.structured_sql).toBe("idle");
    expect(s.statuses.refuse).toBe("idle");
    expect(s.activeNodeId).toBeNull();
    expect(s.model).toBe("llama-3.1-8b-instant");
    expect(s.citations).toEqual([1]);
  });
});

describe("STRUCTURED_SQL branch", () => {
  it("lights only the SQL branch (no evidence, no doc_rag)", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "STRUCTURED_SQL", cache_tier: "MISS" } },
    ];
    const s = pipelineStateFromEvents(events);
    expect(s.route).toBe("STRUCTURED_SQL");
    expect(s.activeNodeId).toBe("structured_sql");
    expect(s.statuses.doc_rag).toBe("idle");
    expect(s.statuses.refuse).toBe("idle");
    expect(s.path).toContain("structured_sql");
    expect(s.path).not.toContain("doc_rag");
  });

  it("completes SQL path on done", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "STRUCTURED_SQL", cache_tier: "MISS" } },
      done({ answer: "There are 250 employees.", citations: [], evidence: [] }),
    ];
    const s = pipelineStateFromEvents(events, false);
    expect(s.statuses.structured_sql).toBe("completed");
    expect(s.statuses.generation).toBe("completed");
    expect(s.statuses.response).toBe("completed");
    expect(s.statuses.doc_rag).toBe("idle");
  });
});

describe("REFUSE branch", () => {
  it("lights only router -> refuse -> response", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "REFUSE", cache_tier: "MISS" } },
    ];
    const s = pipelineStateFromEvents(events);
    expect(s.activeNodeId).toBe("refuse");
    expect(s.path).toEqual(["user", "auth", "authz", "router", "refuse", "response"]);
    expect(s.statuses.doc_rag).toBe("idle");
    expect(s.statuses.structured_sql).toBe("idle");
    expect(s.statuses.generation).toBe("idle");
  });
});

describe("cache hits", () => {
  it("L1: skips router/retrieval/generation, marks cache hit", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: null, cache_tier: "L1" } },
      { event: "evidence", data: EV1 },
      done(),
    ];
    const s = pipelineStateFromEvents(events, false);
    expect(s.cacheHit).toBe(true);
    expect(s.cacheTier).toBe("L1");
    // Retrieval / generation nodes are NEVER lit on a cache hit.
    expect(s.statuses.doc_rag).toBe("idle");
    expect(s.statuses.generation).toBe("idle");
    expect(s.statuses.router).toBe("idle");
    // The cache path completes at response.
    expect(s.statuses.response).toBe("completed");
  });

  it("L2 semantic hit is also a cache hit", () => {
    const s = pipelineStateFromEvents(
      [{ event: "meta", data: { route: null, cache_tier: "L2" } }],
      true,
    );
    expect(s.cacheHit).toBe(true);
    expect(s.cacheTier).toBe("L2");
    expect(s.activeNodeId).toBe("response");
  });

  it("MISS is not a cache hit", () => {
    const s = pipelineStateFromEvents(
      [{ event: "meta", data: { route: "DOCUMENT_RAG", cache_tier: "MISS" } }],
      true,
    );
    expect(s.cacheHit).toBe(false);
  });
});

describe("error handling", () => {
  it("marks the in-flight node failed and clears the active target", () => {
    const events: ChatEvent[] = [
      { event: "meta", data: { route: "DOCUMENT_RAG", cache_tier: "MISS" } },
      { event: "evidence", data: EV1 },
      { event: "error", data: { message: "boom", type: "StreamError" } },
    ];
    const s = pipelineStateFromEvents(events, true);
    expect(s.statuses.generation).toBe("failed");
    expect(s.activeNodeId).toBeNull();
  });
});
