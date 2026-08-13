"use client";

// CachePerformanceCard — L1/L2/Miss rates + avg-latency-saved. Renders
// four small stat blocks in a single panel.
//
// Per the data-viz skill:
//   - text wears text tokens, never the series color
//   - status is communicated with badge variant (success/warning),
//     not with chart color
//   - miss rate badge uses --warning only when its delta is rising
//     and tone is bad; L1/L2 hit rates use --success

import { cacheStats } from "@/lib/mock-data";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

export function CachePerformanceCard() {
  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>Cache performance</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            L1 + L2 hits, miss rate, latency saved
          </p>
        </div>
        <Badge variant="muted">(Demo data)</Badge>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {cacheStats.map((stat) => {
            const tone = stat.unit === "ms"
              ? "good"
              : stat.label === "Cache Miss"
                ? stat.delta && stat.delta.tone === "good"
                  ? "good"
                  : "warning"
                : "good";
            return (
              <div
                key={stat.label}
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/40 p-3"
              >
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                  {stat.label}
                </p>
                <p className="mt-1 text-2xl font-semibold tabular-nums">
                  {stat.unit === "ms" ? stat.value.toLocaleString() : stat.value.toFixed(1)}
                  <span className="ml-1 text-xs font-medium text-[var(--color-muted-foreground)]">
                    {stat.unit}
                  </span>
                </p>
                {stat.delta ? (
                  <p className="mt-1 flex items-center gap-1 text-[11px] text-[var(--color-muted-foreground)]">
                    <Badge variant={tone === "good" ? "success" : "warning"}>
                      {stat.delta.direction === "up" ? "▲" : "▼"}{" "}
                      {Math.abs(stat.delta.percent).toFixed(1)}%
                    </Badge>
                    <span>vs last 7d</span>
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}