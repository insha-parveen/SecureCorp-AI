"use client";

// PipelineConnection — vertical SVG stroke between two pipeline
// nodes. Carries a moving dot when `animated` is true.
//
// Per the data-viz skill: 2px stroke for hairline marks; the moving
// dot is a 2px circle that uses the primary token and rides a CSS
// translate keyframe. Honors prefers-reduced-motion via the global
// override (the dot animation collapses to its first frame).

import * as React from "react";

export interface PipelineConnectionProps {
  /** Index of the source node (0-based). */
  fromIndex: number;
  /** Index of the destination node (0-based). */
  toIndex: number;
  /** When true, the dot animates between the two nodes. */
  animated: boolean;
}

const NODE_HEIGHT = 56; // matches the node padding + content in pipeline-node
const NODE_GAP = 16;    // matches the parent flex gap (gap-4)
const STROKE_HEIGHT = NODE_GAP; // the connector occupies the gap

export function PipelineConnection({
  fromIndex,
  toIndex,
  animated,
}: PipelineConnectionProps) {
  // Only render a connector that goes one step down.
  if (toIndex !== fromIndex + 1) return null;

  return (
    <div
      aria-hidden
      className="relative flex items-center justify-start"
      style={{ height: STROKE_HEIGHT, paddingLeft: 28 }}
    >
      <svg
        viewBox={`0 0 12 ${STROKE_HEIGHT}`}
        width="12"
        height={STROKE_HEIGHT}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id={`pipe-grad-${fromIndex}`} x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="0"
              stopColor={
                animated
                  ? "var(--color-primary)"
                  : "var(--color-muted-foreground)"
              }
              stopOpacity={animated ? 0.9 : 0.4}
            />
            <stop
              offset="1"
              stopColor="var(--color-muted-foreground)"
              stopOpacity="0.2"
            />
          </linearGradient>
        </defs>
        <line
          x1="6"
          y1="0"
          x2="6"
          y2={STROKE_HEIGHT}
          stroke={`url(#pipe-grad-${fromIndex})`}
          strokeWidth="2"
          strokeLinecap="round"
        />
        {animated ? (
          <circle
            cx="6"
            cy={STROKE_HEIGHT / 2}
            r="2.2"
            fill="var(--color-primary)"
            className="pipeline-dot"
          />
        ) : null}
      </svg>
    </div>
  );
}