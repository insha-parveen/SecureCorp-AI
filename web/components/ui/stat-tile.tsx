"use client";

// StatTile — the big-number KPI tile used on /dashboard and /analytics.
// Composes a big value, a delta indicator (color follows TONE, not
// direction), an optional sparkline, and an optional icon. The icon
// is resolved from lucide-react by name; consumer passes the string
// (matches `StatTileData.icon` from dashboard-types).

import * as React from "react";
import {
  Activity,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  type LucideIcon,
  ShieldAlert,
  Sparkles,
  Timer,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "./glass-card";
import { Sparkline as SparklineChart } from "./sparkline";
import type { KpiDelta, StatTileData } from "@/lib/dashboard-types";

// Static icon lookup — keeping the icon registry inside the tile
// avoids forcing consumers to import from lucide-react.
const ICONS: Record<string, LucideIcon> = {
  Activity,
  Timer,
  Zap,
  ShieldAlert,
  Sparkles,
  ArrowUpDown,
};

export interface StatTileProps {
  data: StatTileData;
  className?: string;
}

const toneColor = (tone: KpiDelta["tone"]) => {
  switch (tone) {
    case "good":
      return "text-[var(--color-success)]";
    case "bad":
      return "text-[var(--color-critical)]";
    default:
      return "text-[var(--color-muted-foreground)]";
  }
};

const directionIcon = (dir: KpiDelta["direction"]) => {
  switch (dir) {
    case "up":
      return ArrowUp;
    case "down":
      return ArrowDown;
    default:
      return ArrowUpDown;
  }
};

export function StatTile({ data, className }: StatTileProps) {
  const Icon = data.icon ? ICONS[data.icon] : null;
  const DirIcon = data.delta ? directionIcon(data.delta.direction) : null;
  const deltaSign = data.delta
    ? data.delta.direction === "up"
      ? "+"
      : data.delta.direction === "down"
        ? "−"
        : ""
    : "";

  return (
    <GlassCard className={cn("flex flex-col gap-3 p-4", className)}>
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]">
          {data.label}
        </span>
        {Icon && data.accent && (
          <span
            className="inline-flex size-7 items-center justify-center rounded-md"
            style={{
              backgroundColor: `color-mix(in oklch, ${data.accent} 14%, transparent)`,
              color: data.accent,
            }}
            aria-hidden
          >
            <Icon size={14} strokeWidth={2} />
          </span>
        )}
      </div>
      <div className="flex items-end justify-between gap-2">
        <span className="text-2xl font-semibold tabular-nums text-[var(--color-foreground)]">
          {data.value}
        </span>
        {data.sparkline && data.sparkline.length > 1 && (
          <SparklineChart
            values={data.sparkline}
            color={data.accent ?? "var(--color-primary)"}
            size={84}
            className="opacity-90"
          />
        )}
      </div>
      {data.delta && (
        <div className={cn("flex items-center gap-1 text-xs font-medium", toneColor(data.delta.tone))}>
          {DirIcon && <DirIcon size={12} strokeWidth={2.5} aria-hidden />}
          <span>
            {deltaSign}
            {Math.abs(data.delta.value)} ({deltaSign}
            {data.delta.percent.toFixed(1)}%)
          </span>
          <span className="ml-1 text-[var(--color-muted-foreground)]">vs last 7d</span>
        </div>
      )}
    </GlassCard>
  );
}