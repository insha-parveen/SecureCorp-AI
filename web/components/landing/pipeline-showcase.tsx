"use client";

// LandingPipelineShowcase — drives the REAL <SecureCorpPipeline/> on the
// landing page so the architecture section animates instead of sitting idle.
//
// Why a wrapper (and not just passing a message): the pipeline's reveal
// cursor initializes at "furthest reached", so mounting it with an
// already-complete message shows everything lit at once — no motion. Toggling
// message null → complete (with isStreaming) makes the cursor sweep the whole
// path from the start, exactly like a live request. No logic is duplicated —
// this only feeds props; all node/branch state still comes from the pure
// reducer.
//
// Truthfulness: the driving message is the REAL observed DOCUMENT_RAG run from
// lib/landing-facts (route, cache tier, citations, model). Evidence is left
// empty rather than fabricated, so the node popovers show "Not available" for
// counts we don't carry as structured objects — the sourced "5 chunks" claim
// lives on the hero trace card. prefers-reduced-motion shows the completed
// path statically (no loop).

import * as React from "react";
import { useReducedMotion } from "motion/react";
import { SecureCorpPipeline } from "@/components/pipeline/securecorp-pipeline";
import type { AssistantMessage } from "@/lib/types";
import { EXAMPLE_TRACE } from "@/lib/landing-facts";

// A completed DOCUMENT_RAG run, built from the real example trace.
const SHOWCASE_MESSAGE: AssistantMessage = {
  meta: { route: "DOCUMENT_RAG", cache_tier: "MISS" },
  evidence: [],
  text: "",
  done: {
    answer: "",
    citations: [...EXAMPLE_TRACE.citations],
    evidence: [],
    model: EXAMPLE_TRACE.model,
    usage: {},
    extras: {},
  },
  error: null,
};

// A completed L1 cache-hit run: auth+authz scoping, then the semantic cache
// serves the answer — routing, retrieval, and generation are skipped. This
// demonstrates the semantic cache node lighting up on the landing page.
const CACHE_HIT_MESSAGE: AssistantMessage = {
  meta: { route: null, cache_tier: "L1" },
  evidence: [],
  text: "",
  done: {
    answer: "",
    citations: [],
    evidence: [],
    model: EXAMPLE_TRACE.model,
    usage: {},
    extras: {},
  },
  error: null,
};

// Sweep ≈ 9 path nodes × 420ms cursor interval; freeze after a buffer, hold
// the completed state, then replay.
const SWEEP_MS = 4200;
const HOLD_MS = 2600;
const LEAD_MS = 500;
const CACHE_HOLD_MS = 1800;

export function LandingPipelineShowcase({ title }: { title?: string }) {
  const reduced = useReducedMotion();
  const [message, setMessage] = React.useState<AssistantMessage | null>(null);
  const [streaming, setStreaming] = React.useState(false);

  React.useEffect(() => {
    if (reduced) {
      // Static: show the completed path (arrows lit for the RAG branch).
      setMessage(SHOWCASE_MESSAGE);
      setStreaming(false);
      return;
    }

    let cancelled = false;
    const timers: number[] = [];
    const at = (ms: number, fn: () => void) => timers.push(window.setTimeout(fn, ms));

    const run = () => {
      if (cancelled) return;
      // 1. idle (all nodes dim)
      setMessage(null);
      setStreaming(false);
      // 2. stream: cursor sweeps user → … → response
      at(LEAD_MS, () => {
        if (cancelled) return;
        setMessage(SHOWCASE_MESSAGE);
        setStreaming(true);
      });
      // 3. freeze the completed state
      at(LEAD_MS + SWEEP_MS, () => {
        if (cancelled) return;
        setStreaming(false);
      });
      // 4. hold the RAG path, then show a cache hit
      at(LEAD_MS + SWEEP_MS + HOLD_MS, () => {
        if (cancelled) return;
        setMessage(CACHE_HIT_MESSAGE);
        setStreaming(false);
      });
      // 5. hold the cache hit, then replay
      at(LEAD_MS + SWEEP_MS + HOLD_MS + CACHE_HOLD_MS, run);
    };
    run();

    return () => {
      cancelled = true;
      timers.forEach((t) => window.clearTimeout(t));
    };
  }, [reduced]);

  return <SecureCorpPipeline title={title} message={message} isStreaming={streaming} />;
}
