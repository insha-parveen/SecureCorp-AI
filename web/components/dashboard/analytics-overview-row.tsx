"use client";

// AnalyticsOverviewRow — the 2×2 grid of stat tiles used as the top
// row of the /dashboard home tile grid. Each tile is a StatTile built
// from real-time analytics fetched via /api/analytics/overview.
//
// Layout note: 2 columns on md, 4 columns on xl — the reference
// surface shows four tiles fitting comfortably across the top. The
// md/2-col breakpoint is a graceful fallback on narrower viewports.

import { useQuery } from "@tanstack/react-query";
import { getAnalyticsOverview } from "@/lib/api";
import { StatTile } from "@/components/ui/stat-tile";
import type { StatTileData } from "@/lib/dashboard-types";

export function AnalyticsOverviewRow() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: getAnalyticsOverview,
  });

  if (isLoading) {
    return (
      <section aria-label="System metrics overview">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-[var(--color-muted)]/30" />
          ))}
        </div>
      </section>
    );
  }

  if (isError || !data) {
    return null;
  }

  const tiles: StatTileData[] = [
    {
      label: "Total Queries",
      value: data.total_queries.toLocaleString(),
      rawValue: data.total_queries,
      accent: "var(--color-series-1)",
      icon: "Activity",
    },
    {
      label: "Avg. Response Time",
      value: `${data.avg_latency}s`,
      rawValue: data.avg_latency,
      accent: "var(--color-series-3)",
      icon: "Timer",
    },
    {
      label: "Cache Hit Rate",
      value: `${data.cache_hit_rate}%`,
      rawValue: data.cache_hit_rate,
      accent: "var(--color-series-4)",
      icon: "Zap",
    },
    {
      label: "Refused / Blocked",
      value: `${data.refusal_rate}%`,
      rawValue: data.refusal_rate,
      accent: "var(--color-critical)",
      icon: "ShieldAlert",
    },
  ];

  return (
    <section aria-label="System metrics overview">
      <header className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
          System metrics
        </h2>
        <span className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
          Real-time data
        </span>
      </header>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {tiles.map((tile) => (
          <StatTile key={tile.label} data={tile} />
        ))}
      </div>
    </section>
  );
}
