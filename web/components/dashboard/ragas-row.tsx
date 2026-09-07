"use client";

// RagasRow — four gauges, one per RAGAS metric. Highlighted gauge
// uses a thicker ring per the data-viz mark spec.
//
// Values come from lib/mock-data.ts. When the backend exposes RAGAS through
// /api/analytics, swap to that fetch without changing this component's shape.

import { ragasGauges } from "@/lib/mock-data";
import { Gauge } from "@/components/ui/gauge";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";

export function RagasRow() {
  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>RAGAS evaluation</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Offline quality metrics — last 7 days
          </p>
        </div>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {ragasGauges.map((g) => (
            <div
              key={g.label}
              className="flex flex-col items-center gap-1"
            >
              <Gauge
                value={g.value}
                max={1}
                label={g.label}
                highlighted={g.highlighted}
                accent={
                  g.highlighted
                    ? "var(--color-primary)"
                    : "var(--color-series-1)"
                }
                size={120}
              />
            </div>
          ))}
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}