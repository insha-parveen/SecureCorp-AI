"use client";

// RetrievalProbe — the retrieval section's centerpiece (CLAUDE.md §7). Shows
// the hybrid pipeline stages and the identifier-recall diagnostic that
// justifies keeping BM25 (hit@1 40/40 vs dense 4/40). Per the honesty rule,
// the probe is LABELED a diagnostic, never a benchmark, and its caveat is
// rendered inline — this is the number that most needs its context attached.

import * as React from "react";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardTitle,
} from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { BM25_PROBE, RETRIEVAL_CONFIG, RETRIEVAL_STAGES } from "@/lib/landing-facts";

export function RetrievalProbe() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* The pipeline stages, in order. */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Hybrid pipeline</GlassCardTitle>
        </GlassCardHeader>
        <GlassCardContent className="space-y-3">
          {RETRIEVAL_STAGES.map((stage, i) => (
            <div key={stage.name} className="flex items-start gap-3">
              <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border border-[var(--color-border)] bg-[var(--color-muted)]/50 font-mono text-[11px] text-[var(--color-muted-foreground)]">
                {i + 1}
              </span>
              <div>
                <span className="font-mono text-sm font-medium text-[var(--color-foreground)]">
                  {stage.name}
                </span>
                <p className="text-[13px] text-[var(--color-muted-foreground)]">{stage.detail}</p>
              </div>
            </div>
          ))}
          <div className="mt-2 flex flex-wrap gap-2 border-t border-[var(--color-border)] pt-3 font-mono text-[11px] text-[var(--color-muted-foreground)]">
            <span>RRF k={RETRIEVAL_CONFIG.rrfK}</span>
            <span>·</span>
            <span>BM25 k1={RETRIEVAL_CONFIG.bm25K1} b={RETRIEVAL_CONFIG.bm25B}</span>
            <span>·</span>
            <span>{RETRIEVAL_CONFIG.embeddingDims}-dim {RETRIEVAL_CONFIG.distance}</span>
          </div>
        </GlassCardContent>
      </GlassCard>

      {/* The diagnostic probe — explicitly not a benchmark. */}
      <GlassCard>
        <GlassCardHeader className="flex-row items-center justify-between space-y-0">
          <GlassCardTitle>Why BM25 earns its place</GlassCardTitle>
          <Badge variant="muted">Diagnostic probe</Badge>
        </GlassCardHeader>
        <GlassCardContent className="space-y-4">
          <p className="text-[13px] text-[var(--color-muted-foreground)]">
            Probing all {BM25_PROBE.identifiers} identifiers that occur in
            exactly one chunk — asking each retriever for the chunk containing
            it:
          </p>
          <div className="grid grid-cols-2 gap-3">
            <ProbeBar
              label="BM25 hit@1"
              hits={BM25_PROBE.bm25HitAt1}
              total={BM25_PROBE.identifiers}
              tone="var(--color-success)"
            />
            <ProbeBar
              label="Dense hit@1"
              hits={BM25_PROBE.denseHitAt1}
              total={BM25_PROBE.identifiers}
              tone="var(--color-series-2)"
            />
          </div>
          <p className="font-mono text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
            {BM25_PROBE.caveat}
          </p>
        </GlassCardContent>
      </GlassCard>
    </div>
  );
}

// A labeled horizontal bar showing hits/total. Value in mono; the fill uses
// the caller-supplied token color (success for BM25, cyan for dense).
function ProbeBar({
  label,
  hits,
  total,
  tone,
}: {
  label: string;
  hits: number;
  total: number;
  tone: string;
}) {
  const pct = Math.round((hits / total) * 100);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] uppercase tracking-wide text-[var(--color-muted-foreground)]">
          {label}
        </span>
        <span className="font-mono text-sm font-semibold tabular-nums" style={{ color: tone }}>
          {hits}/{total}
        </span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full bg-[var(--color-muted)]"
        role="img"
        aria-label={`${label}: ${hits} of ${total}`}
      >
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: tone }} />
      </div>
    </div>
  );
}
