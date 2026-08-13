"use client";

// QueryTypesDonut — three-segment donut (Document RAG / SQL /
// Refused). Hand-rolled inline SVG using the <Donut/> primitive.
//
// Per the data-viz skill:
//   - categorical hues in fixed order (never cycled)
//   - 2px surface gap between fills (Donut applies this internally)
//   - legend always present for ≥2 series
//   - text wears text tokens, never series color

import { useQuery } from "@tanstack/react-query";
import { Donut, DonutLegend } from "@/components/ui/donut";
import { getQueryTypes } from "@/lib/api";
import { queryTypes as mockQueryTypes } from "@/lib/mock-data";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

export function QueryTypesDonut() {
  // Fetch real routing breakdown; fall back to demo data when empty.
  const { data: fetched } = useQuery({
    queryKey: ["query-types"],
    queryFn: getQueryTypes,
  });
  const isLive = Boolean(fetched && fetched.length > 0);
  const segments = isLive ? fetched! : mockQueryTypes;
  const total = segments.reduce((acc, s) => acc + s.value, 0);

  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>Query types</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Routing breakdown (last 7 days)
          </p>
        </div>
        <Badge variant="muted">{isLive ? "Live" : "(Demo data)"}</Badge>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="flex flex-col items-center gap-4 md:flex-row">
          <Donut
            segments={segments}
            size={160}
            centerLabel={isLive ? "Share" : "Total"}
            centerValue={isLive ? `${Math.round(total)}%` : "1,248"}
          />
          <DonutLegend segments={segments} className="md:flex-1" />
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}