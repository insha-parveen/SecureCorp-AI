"use client";

// SystemMetrics — alternate name for the same KPI row. Used when the
// /dashboard surface wants the tiles presented as a 2×2 (or 4×1) grid
// rather than the analytics overview's framing. Aliased separately so
// each consumer (analytics-overview-row vs. system-metrics) can evolve
// without affecting the other.

import { kpiTiles } from "@/lib/mock-data";
import { StatTile } from "@/components/ui/stat-tile";

export function SystemMetrics() {
  return (
    <section aria-label="System metrics">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {kpiTiles.map((tile) => (
          <StatTile key={tile.label} data={tile} />
        ))}
      </div>
    </section>
  );
}