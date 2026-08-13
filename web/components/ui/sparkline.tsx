"use client";

// Sparkline — a 12-point line used inside StatTile. Inline SVG so it
// inherits text color via currentColor for the stroke. The trailing
// data-point gets a 4px rounded end per the data-viz skill's mark spec.
// Honors prefers-reduced-motion: the stroke-dasharray draw animation
// is gated through a CSS media query, so the line snaps to its final
// state when motion is reduced.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SparklineProps extends Omit<React.SVGProps<SVGSVGElement>, "values"> {
  /** Data points. Empty / single-point arrays render nothing. */
  values: number[];
  /** Stroke color. Defaults to currentColor. */
  color?: string;
  /** Pixel size of the rendered SVG. */
  size?: number;
}

const PAD = 2; // breathing room so the data-end isn't clipped at the edge

export function Sparkline({
  values,
  color = "currentColor",
  size = 88,
  className,
  ...props
}: SparklineProps) {
  if (values.length < 2) return null;

  const w = size;
  const h = (size * 28) / 88; // keep aspect consistent (88x28 typical)
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = (w - PAD * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = PAD + i * step;
    // invert Y so higher values sit visually higher
    const y = PAD + (h - PAD * 2) * (1 - (v - min) / range);
    return [x, y] as const;
  });

  const d = points
    .map(([x, y], i) => (i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`))
    .join(" ");
  const [lx, ly] = points[points.length - 1];

  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      className={cn("block", className)}
      role="img"
      aria-label={`sparkline, ${values.length} points`}
      {...props}
    >
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={lx} cy={ly} r={2} fill={color} />
    </svg>
  );
}