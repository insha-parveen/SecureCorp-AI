"use client";

// usePipelineAnimation — drives the active-node index for PipelineFlow.
// Two modes:
//
//   1. Static: pass `steps` with their own `status` already set. The
//      hook just returns them. Useful on /dashboard where the pipeline
//      shows a fixed "last completed run" snapshot.
//
//   2. Animated: pass `streaming` (boolean). While false, the active
//      node is null (no animation). While true, the active node ticks
//      through the steps at a steady cadence (~600ms per step). The
//      hook cleans up the timer on unmount.
//
// Per §24.5 prefers-reduced-motion is honored by reading the OS
// preference: when the user opts out, the hook skips the timer and
// jumps to the last step (signaling "complete") so the chart
// communicates the same final state without animation.

import * as React from "react";
import type { PipelineStep } from "@/lib/dashboard-types";

export interface UsePipelineAnimationOptions {
  steps: PipelineStep[];
  /** When true, the pipeline animates through the steps. */
  streaming?: boolean;
  /** ms per step. Defaults to 600. */
  intervalMs?: number;
}

const PREFERS_REDUCED_MOTION =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export function usePipelineAnimation({
  steps,
  streaming = false,
  intervalMs = 600,
}: UsePipelineAnimationOptions): PipelineStep[] {
  const [activeIndex, setActiveIndex] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (!streaming) {
      setActiveIndex(null);
      return;
    }
    if (PREFERS_REDUCED_MOTION) {
      // Skip the animation: jump to the last step as "complete".
      setActiveIndex(steps.length - 1);
      return;
    }
    setActiveIndex(0);
    const id = window.setInterval(() => {
      setActiveIndex((prev) => {
        if (prev === null) return 0;
        return prev + 1 >= steps.length ? steps.length - 1 : prev + 1;
      });
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [streaming, steps.length, intervalMs]);

  return React.useMemo(() => {
    if (!streaming) return steps;
    if (activeIndex === null) return steps;
    return steps.map((step, i) => {
      if (i < activeIndex) return { ...step, status: "done" };
      if (i === activeIndex) return { ...step, status: "active" };
      return { ...step, status: "pending" };
    });
  }, [steps, streaming, activeIndex]);
}