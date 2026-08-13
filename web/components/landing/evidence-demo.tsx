"use client";

// EvidenceDemo — the evidence section (CLAUDE.md §5 generation invariants).
// Shows that a citation is not a decoration: it resolves to a real, indexed
// chunk_id, validated server-side. Two real traces from the 2026-08-12 e2e
// run: a RAG answer whose citations resolve, and the structured-SQL branch
// (proving the non-vector path). Reuses the TraceCard signature.

import * as React from "react";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardTitle,
} from "@/components/ui/glass-card";
import { TraceCard } from "@/components/landing/trace-card";
import { EXAMPLE_TRACE, EXAMPLE_SQL_TRACE } from "@/lib/landing-facts";

export function EvidenceDemo() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Citations resolve to a real chunk. */}
      <div className="space-y-4">
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Citations resolve to evidence</GlassCardTitle>
          </GlassCardHeader>
          <GlassCardContent className="space-y-3">
            <p className="text-[13px] leading-relaxed text-[var(--color-muted-foreground)]">
              The model may cite only evidence IDs the application supplied.
              Every returned citation is validated server-side and must resolve
              to an indexed chunk — unknown IDs are rejected. If evidence is
              insufficient, the system abstains instead of fabricating.
            </p>
            <div className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)]/30 px-3 py-2.5">
              <span className="font-mono text-sm font-semibold text-[var(--color-success)]">
                [{EXAMPLE_TRACE.citations[0]}]
              </span>
              <span className="text-[var(--color-muted-foreground)]" aria-hidden>
                →
              </span>
              <span className="font-mono text-[13px] text-[var(--color-foreground)]">
                {EXAMPLE_TRACE.topChunkId}
              </span>
            </div>
          </GlassCardContent>
        </GlassCard>
      </div>

      {/* The structured-SQL branch — a different, real trace. */}
      <TraceCard
        label="structured query · example"
        prompt={EXAMPLE_SQL_TRACE.query}
        lines={[
          { key: "user", value: `${EXAMPLE_SQL_TRACE.user} (${EXAMPLE_SQL_TRACE.roles})`, tone: "value" },
          { key: "authz", value: EXAMPLE_SQL_TRACE.authz, tone: "pass", ok: true },
          { key: "route", value: EXAMPLE_SQL_TRACE.route, tone: "route-sql" },
          { key: "cache", value: EXAMPLE_SQL_TRACE.cacheTier, tone: "muted" },
          { key: "db", value: "PostgreSQL (template SQL)", tone: "value" },
          { key: "answer", value: EXAMPLE_SQL_TRACE.answer, tone: "value" },
        ]}
        footer={EXAMPLE_SQL_TRACE.source}
      />
    </div>
  );
}
