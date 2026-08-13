// Unit tests for the SecureCorp pipeline node + detail popover.
// Verifies: each NodeStatus renders an accessible label, interactive nodes
// are buttons, and the detail popover shows "Not available" for fields the
// backend didn't provide (the "never invent data" rule).

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SecureCorpPipelineNode } from "@/components/pipeline/securecorp-pipeline-node";
import { PipelineDetail } from "@/components/pipeline/pipeline-detail";
import { nodeDetail, derivePipelineState, NOT_AVAILABLE } from "@/lib/pipeline-state";

describe("SecureCorpPipelineNode", () => {
  it("exposes an aria-label with the status", () => {
    render(
      <SecureCorpPipelineNode label="Authorization" icon="ShieldCheck" status="processing" accent="neutral" />,
    );
    expect(screen.getByLabelText("Authorization — processing")).toBeTruthy();
  });

  it("is a button when interactive and reports expanded state", () => {
    render(
      <SecureCorpPipelineNode
        label="Query Router"
        icon="GitBranch"
        status="completed"
        accent="neutral"
        onActivate={() => {}}
        expanded
      />,
    );
    const btn = screen.getByRole("button", { name: /Query Router/ });
    expect(btn.getAttribute("aria-expanded")).toBe("true");
  });

  it("renders each status without crashing", () => {
    for (const status of ["idle", "processing", "completed", "failed"] as const) {
      const { unmount } = render(
        <SecureCorpPipelineNode label={`N-${status}`} icon="Circle" status={status} accent="rag" />,
      );
      expect(screen.getByLabelText(`N-${status} — ${status}`)).toBeTruthy();
      unmount();
    }
  });
});

describe("PipelineDetail", () => {
  it("renders 'Not available' for fields the backend didn't provide", () => {
    // A RAG state with no done event: candidate/reranked counts are NA.
    const state = derivePipelineState(
      {
        meta: { route: "DOCUMENT_RAG", cache_tier: "MISS" },
        evidence: [],
        text: "",
        done: null,
        error: null,
      },
      true,
    );
    const detail = nodeDetail("doc_rag", state, null);
    render(<PipelineDetail detail={detail} onClose={() => {}} />);
    // Candidates + Reranked are always NA (not on the wire).
    expect(screen.getAllByText(NOT_AVAILABLE).length).toBeGreaterThanOrEqual(2);
  });

  it("shows the real model name when the done event carried one", () => {
    const state = derivePipelineState(
      {
        meta: { route: "DOCUMENT_RAG", cache_tier: "MISS" },
        evidence: [],
        text: "answer",
        done: {
          answer: "answer",
          citations: [1],
          evidence: [],
          model: "llama-3.1-8b-instant",
          usage: {},
          extras: {},
        },
        error: null,
      },
      false,
    );
    const detail = nodeDetail("generation", state, null);
    render(<PipelineDetail detail={detail} onClose={() => {}} />);
    expect(screen.getByText("llama-3.1-8b-instant")).toBeTruthy();
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    const state = derivePipelineState(null, false);
    render(<PipelineDetail detail={nodeDetail("user", state, null)} onClose={onClose} />);
    screen.getByLabelText("Close details").click();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
