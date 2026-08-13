"use client";

// /analytics — long-scroll mirror of the dashboard. Reuses every panel
// built in #27 + the chunking sweep + the 4-arm ablation chart.
//
// Chunking sweep table: 4 grid cells × 4 arms. Each cell shows the
// Hybrid-Rerank arm's recall@5 plus a compact cost-per-query metric.
// Mock values — when the backend exposes /api/chunking-sweep, swap
// to that fetch without changing the panel.

import { PageHeader } from "@/components/layout/page-header";
import { RetrievalTable } from "@/components/dashboard/retrieval-table";
import { RagasRow } from "@/components/dashboard/ragas-row";
import { SecurityIsolationCard } from "@/components/dashboard/security-isolation-card";
import { CachePerformanceCard } from "@/components/dashboard/cache-performance-card";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

interface SweepCell {
  cellId: string;
  target: number;
  overlap: number;
  min: number;
  chunks: number;
  recallAt5: number;
  latencyP95Ms: number;
}

// 4 cells from the chunking sweep (matches Phase 8 grid).
const CHUNKING_SWEEP: SweepCell[] = [
  { cellId: "baseline", target: 440, overlap: 60, min: 300, chunks: 450, recallAt5: 0.94, latencyP95Ms: 320 },
  { cellId: "dense_coarse", target: 512, overlap: 64, min: 256, chunks: 412, recallAt5: 0.92, latencyP95Ms: 295 },
  { cellId: "fine_overlap", target: 320, overlap: 80, min: 200, chunks: 538, recallAt5: 0.91, latencyP95Ms: 360 },
  { cellId: "long_overlap", target: 512, overlap: 128, min: 256, chunks: 384, recallAt5: 0.95, latencyP95Ms: 410 },
];

export default function AnalyticsPage() {
  return (
    <>
      <PageHeader title="Analytics" eyebrow="Performance" />
      <div className="space-y-6 p-4 sm:p-6">
        <RetrievalTable />

        <RagasRow />

        <GlassCard>
          <GlassCardHeader className="flex-row items-center justify-between space-y-0">
            <div className="flex flex-col gap-1">
              <GlassCardTitle>Chunking sweep</GlassCardTitle>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                4-cell grid on the Hybrid-Rerank arm (n=30 frozen subset)
              </p>
            </div>
            <Badge variant="muted">(Demo data)</Badge>
          </GlassCardHeader>
          <GlassCardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="py-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                      Cell
                    </th>
                    <th className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                      target / overlap / min
                    </th>
                    <th className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                      chunks
                    </th>
                    <th className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                      Recall@5
                    </th>
                    <th className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                      p95 (ms)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {CHUNKING_SWEEP.map((cell) => (
                    <tr
                      key={cell.cellId}
                      className={`border-b border-[var(--color-border)]/60 last:border-b-0 ${
                        cell.cellId === "baseline"
                          ? "bg-[color-mix(in_oklch,var(--color-primary)_6%,transparent)]"
                          : ""
                      }`}
                    >
                      <th scope="row" className="py-2 pr-4 text-left">
                        <span className="inline-flex items-center gap-2">
                          <span>{cell.cellId}</span>
                          {cell.cellId === "baseline" ? (
                            <Badge variant="accent">Production</Badge>
                          ) : null}
                        </span>
                      </th>
                      <td className="py-2 px-2 text-right font-mono tabular-nums">
                        {cell.target} / {cell.overlap} / {cell.min}
                      </td>
                      <td className="py-2 px-2 text-right font-mono tabular-nums">
                        {cell.chunks}
                      </td>
                      <td className="py-2 px-2 text-right font-mono tabular-nums">
                        {cell.recallAt5.toFixed(2)}
                      </td>
                      <td className="py-2 px-2 text-right font-mono tabular-nums">
                        {cell.latencyP95Ms}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[11px] text-[var(--color-muted-foreground)]">
              Production index is left untouched during the sweep — see{" "}
              <code className="font-mono text-[10px]">scripts/run_chunking_sweep.py</code>.
            </p>
          </GlassCardContent>
        </GlassCard>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SecurityIsolationCard />
          <CachePerformanceCard />
        </div>
      </div>
    </>
  );
}
