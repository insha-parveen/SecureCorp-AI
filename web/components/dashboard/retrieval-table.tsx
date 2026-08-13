"use client";

// RetrievalTable — 4 rows × 5 cols of the retrieval arms. The
// "Hybrid + Rerank" row is highlighted because its recall@5 / MRR@10
// values are the actual Phase 8 measurement (cited in mock-data.ts).
// Other rows are illustrative ablations.
//
// Per the data-viz skill: text wears text tokens, never the series
// color. The highlighted row uses the `--primary` ring + a hairline
// band, not a fill swap. Status (winning) is communicated with
// position + ring, not with red/green.

import { retrievalRows } from "@/lib/mock-data";
import type { RetrievalRow } from "@/lib/dashboard-types";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const COLUMNS: { key: keyof RetrievalRow; label: string; format: (v: number) => string }[] = [
  { key: "recallAt5", label: "Recall@5", format: (v) => v.toFixed(2) },
  { key: "mrrAt10", label: "MRR@10", format: (v) => v.toFixed(2) },
  { key: "hitAt1", label: "Hit@1", format: (v) => v.toFixed(2) },
  { key: "ndcgAt10", label: "nDCG@10", format: (v) => v.toFixed(2) },
  { key: "precisionAt5", label: "Precision@5", format: (v) => v.toFixed(2) },
];

export function RetrievalTable() {
  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>Retrieval performance</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Per-arm comparison on the development split (n=240)
          </p>
        </div>
        <Badge variant="muted">
          Phase 8 · dev split
        </Badge>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th
                  scope="col"
                  className="py-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]"
                >
                  Method
                </th>
                {COLUMNS.map((c) => (
                  <th
                    key={c.key}
                    scope="col"
                    className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]"
                  >
                    {c.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {retrievalRows.map((row) => (
                <tr
                  key={row.method}
                  className={cn(
                    "border-b border-[var(--color-border)]/60 last:border-b-0",
                    row.highlighted && "bg-[color-mix(in_oklch,var(--color-primary)_6%,transparent)]",
                  )}
                >
                  <th scope="row" className="py-2 pr-4 text-left">
                    <span className="inline-flex items-center gap-2">
                      <span>{row.method}</span>
                      {row.highlighted ? (
                        <Badge variant="accent">Best</Badge>
                      ) : null}
                    </span>
                  </th>
                  {COLUMNS.map((c) => (
                    <td
                      key={c.key}
                      className="py-2 px-2 text-right font-mono tabular-nums"
                    >
                      {c.format(row[c.key] as number)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}