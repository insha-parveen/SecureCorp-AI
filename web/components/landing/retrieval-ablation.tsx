"use client";

// RetrievalAblation — the measured payoff of the hybrid pipeline. Unlike the
// diagnostic probe next to it, these ARE the Phase-8 retrieval-quality numbers:
// real harness output on the answerable holdout split, authorization enforced,
// with RRF k=10 + the identifier-aware reranker bypass live. Hybrid (RRF) is
// highlighted because it is the best arm and the one the system ships.

import * as React from "react";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardTitle,
} from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { RETRIEVAL_ABLATION_HOLDOUT, RETRIEVAL_HEADLINE } from "@/lib/landing-facts";

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export function RetrievalAblation() {
  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <GlassCardTitle>Does hybrid actually win?</GlassCardTitle>
        <Badge variant="muted">Holdout · authorized</Badge>
      </GlassCardHeader>
      <GlassCardContent className="space-y-4">
        <p className="text-[13px] text-[var(--color-muted-foreground)]">
          Measured on the answerable holdout split with authorization enforced —
          the production path, not a raw-retrieval demo. Fusion beats both of its
          own inputs; the peak arm reaches{" "}
          <span className="font-semibold text-[var(--color-foreground)]">
            {RETRIEVAL_HEADLINE.bestRecallAt5} Recall@5
          </span>{" "}
          on the dev set (measured ceiling {RETRIEVAL_HEADLINE.ceiling}).
        </p>

        <div className="overflow-hidden rounded-lg border border-[var(--color-border)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] bg-[var(--color-muted)]/40 text-[11px] uppercase tracking-wide text-[var(--color-muted-foreground)]">
                <th className="px-3 py-2 text-left font-medium">Strategy</th>
                <th className="px-3 py-2 text-right font-medium">Recall@5</th>
                <th className="px-3 py-2 text-right font-medium">Hit@1</th>
              </tr>
            </thead>
            <tbody>
              {RETRIEVAL_ABLATION_HOLDOUT.map((row) => (
                <tr
                  key={row.strategy}
                  className="border-b border-[var(--color-border)] last:border-0"
                >
                  <td className="px-3 py-2">
                    <span className="flex items-center gap-2">
                      <span
                        className={
                          row.best
                            ? "font-semibold text-[var(--color-foreground)]"
                            : "text-[var(--color-muted-foreground)]"
                        }
                      >
                        {row.strategy}
                      </span>
                      {row.best ? <Badge variant="accent">Best</Badge> : null}
                    </span>
                  </td>
                  <td
                    className="px-3 py-2 text-right font-mono tabular-nums"
                    style={row.best ? { color: "var(--color-success)" } : undefined}
                  >
                    {pct(row.recallAt5)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums text-[var(--color-muted-foreground)]">
                    {pct(row.hitAt1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="font-mono text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
          Real harness output · {RETRIEVAL_HEADLINE.source}
        </p>
      </GlassCardContent>
    </GlassCard>
  );
}
