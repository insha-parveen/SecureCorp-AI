// Donut — a 3-segment donut chart (semantic aggregate). Used by the
// Query Types panel (Document RAG / SQL / Refused). Inline SVG, no
// chart library. The math:
//
//   - sweep = (value / total) * 360
//   - each arc is drawn from the previous segment's end angle
//   - the gap between segments is 2px (per the data-viz mark spec:
//     "2px surface gap between fills")
//   - segments are coloured in the order given (never cycled / rotated),
//     so the categorical mapping stays stable across the dashboard.
//
// When the segments sum to 0 (no data), this renders a single dim
// placeholder ring instead of blowing up the math.

import * as React from "react";
import { cn } from "@/lib/utils";
import type { DonutSegment } from "@/lib/dashboard-types";

export interface DonutProps {
  segments: DonutSegment[];
  /** Center label (e.g. total queries). */
  centerLabel?: string;
  /** Center value (e.g. "1,248"). */
  centerValue?: string;
  size?: number;
  className?: string;
}

const STROKE = 14;
const GAP = 2; // degrees between segments — translated to a 2px-ish gap at our radius

export function Donut({
  segments,
  centerLabel,
  centerValue,
  size = 140,
  className,
}: DonutProps) {
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - STROKE) / 2 - 2;
  const total = segments.reduce((acc, s) => acc + s.value, 0);
  const hasData = total > 0;

  const toRad = (deg: number) => ((deg - 90) * Math.PI) / 180;
  const polar = (deg: number) => {
    const a = toRad(deg);
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as const;
  };

  return (
    <div
      className={cn("inline-flex flex-col items-center gap-2", className)}
      role="img"
      aria-label={segments.map((s) => `${s.label} ${s.value}%`).join(", ")}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="block">
        {!hasData ? (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={STROKE}
          />
        ) : (
          (() => {
            let cursor = 0;
            return segments.map((seg) => {
              const sweep = (seg.value / total) * 360;
              const start = cursor + GAP / 2;
              const end = cursor + sweep - GAP / 2;
              cursor += sweep;
              if (sweep <= 0) return null;
              const [sx, sy] = polar(start);
              const [ex, ey] = polar(end);
              const large = end - start > 180 ? 1 : 0;
              const d = `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`;
              return (
                <path
                  key={seg.label}
                  d={d}
                  fill="none"
                  stroke={seg.color}
                  strokeWidth={STROKE}
                  strokeLinecap="butt"
                />
              );
            });
          })()
        )}
      </svg>
      {(centerValue || centerLabel) && (
        <div className="-mt-20 flex flex-col items-center gap-0.5">
          {centerValue && (
            <span className="text-base font-semibold tabular-nums text-[var(--color-foreground)]">
              {centerValue}
            </span>
          )}
          {centerLabel && (
            <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]">
              {centerLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export function DonutLegend({
  segments,
  className,
}: {
  segments: DonutSegment[];
  className?: string;
}) {
  return (
    <ul className={cn("flex flex-col gap-1.5 text-xs", className)}>
      {segments.map((s) => (
        <li key={s.label} className="flex items-center gap-2">
          <span
            className="inline-block size-2 rounded-full"
            style={{ backgroundColor: s.color }}
            aria-hidden
          />
          <span className="text-[var(--color-foreground)]">{s.label}</span>
          <span className="ml-auto tabular-nums text-[var(--color-muted-foreground)]">
            {s.value}%
          </span>
        </li>
      ))}
    </ul>
  );
}