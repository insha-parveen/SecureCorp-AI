// Gauge — a ¾-circle (270°) SVG gauge. Used by the RAGAS panel for
// Faithfulness / Answer Relevancy / Context Precision / Context Recall.
//
// Props:
//   value   in [0, 1]  — the metric value
//   max     in [0, 1]  — default 1
//   label   string     — appears in the center under the value
//   accent  CSS color  — the colored ring stroke; defaults to --primary
//   highlighted        — when true, the ring is slightly thicker and the
//                        inner number is in the accent color (used for the
//                        headlining metric, e.g. Context Recall).
//
// The stroke draws from the 7-o'clock to the 5-o'clock position via
// stroke-dasharray. The animation is intentionally simple — a CSS
// transition on stroke-dashoffset — so prefers-reduced-motion (already
// collapsing animations in theme.css) will halt it without any extra
// JS code here.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface GaugeProps {
  value: number;
  max?: number;
  label: string;
  accent?: string;
  highlighted?: boolean;
  size?: number;
  className?: string;
}

const TRACK = 8; // stroke width of the background ring
const RING = 4; // stroke width of the value ring

export function Gauge({
  value,
  max = 1,
  label,
  accent = "var(--color-primary)",
  highlighted = false,
  size = 120,
  className,
}: GaugeProps) {
  // ¾-circle: arc spans 270° (from 135° to 45°) leaving a gap at the bottom.
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - Math.max(TRACK, RING)) / 2 - 2;
  const startAngle = 135;
  const sweep = 270;

  // polar -> cartesian for ARC paths
  const toRad = (deg: number) => ((deg - 90) * Math.PI) / 180;
  const polar = (deg: number) => {
    const a = toRad(deg);
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as const;
  };

  const [sx, sy] = polar(startAngle);
  const [ex, ey] = polar(startAngle + sweep);
  const largeArc = sweep > 180 ? 1 : 0;
  const trackPath = `M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${ex} ${ey}`;

  const clamped = Math.max(0, Math.min(value, max));
  const ratio = clamped / max;
  const valueSweep = sweep * ratio;
  const valuePath = (() => {
    if (ratio === 0) return "";
    if (ratio === 1) {
      // full sweep — same start, end; visually a single arc closing the gap
      const [fsx, fsy] = polar(startAngle);
      return `M ${fsx} ${fsy} A ${r} ${r} 0 1 1 ${fsx} ${fsy}`;
    }
    const [vsx, vsy] = polar(startAngle);
    const [vex, vey] = polar(startAngle + valueSweep);
    const vLarge = valueSweep > 180 ? 1 : 0;
    return `M ${vsx} ${vsy} A ${r} ${r} 0 ${vLarge} 1 ${vex} ${vey}`;
  })();

  const displayValue = (clamped * 100).toFixed(0);

  return (
    <div
      className={cn("inline-flex flex-col items-center gap-1", className)}
      role="img"
      aria-label={`${label}: ${displayValue} percent`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="block">
        {/* track */}
        <path
          d={trackPath}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={TRACK}
          strokeLinecap="round"
        />
        {/* value */}
        {valuePath ? (
          <path
            d={valuePath}
            fill="none"
            stroke={accent}
            strokeWidth={highlighted ? RING + 1 : RING}
            strokeLinecap="round"
            style={{
              transition: "stroke-dashoffset 200ms ease-out",
            }}
          />
        ) : null}
      </svg>
      <div className="-mt-12 flex flex-col items-center gap-0.5">
        <span
          className={cn(
            "text-lg font-semibold tabular-nums",
            highlighted ? "" : "text-[var(--color-foreground)]",
          )}
          style={highlighted ? { color: accent } : undefined}
        >
          {displayValue}
          <span className="text-xs text-[var(--color-muted-foreground)]">%</span>
        </span>
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]">
          {label}
        </span>
      </div>
    </div>
  );
}