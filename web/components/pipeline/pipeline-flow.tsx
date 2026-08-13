"use client";

// PipelineFlow — the vertical 11-node chain that visualizes the
// retrieval + generation path. Used by:
//
//   - /chat: pass `streaming={isStreaming}` to animate live
//   - /dashboard: pass no streaming flag for a static "last run" view
//
// Per §24.5 prefers-reduced-motion is honored by usePipelineAnimation
// (skips the timer and jumps to the final step). Honors the data-viz
// mark spec — 2px strokes, status via icon color not text.

import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { PipelineNode } from "@/components/pipeline/pipeline-node";
import { PipelineConnection } from "@/components/pipeline/pipeline-connection";
import { usePipelineAnimation } from "@/hooks/use-pipeline-animation";
import type { PipelineStep } from "@/lib/dashboard-types";

export interface PipelineFlowProps {
  /** The list of pipeline steps to render. */
  steps: PipelineStep[];
  /** When true, the pipeline ticks through the steps. */
  streaming?: boolean;
  /** ms per step while streaming. */
  intervalMs?: number;
  /** Optional header label. */
  title?: string;
}

export function PipelineFlow({
  steps,
  streaming = false,
  intervalMs,
  title = "How this answer was generated",
}: PipelineFlowProps) {
  const animatedSteps = usePipelineAnimation({
    steps,
    streaming,
    intervalMs,
  });

  // The active step's index drives which connector animates.
  const activeIndex = animatedSteps.findIndex((s) => s.status === "active");

  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <GlassCardTitle>{title}</GlassCardTitle>
        {streaming ? (
          <Badge variant="accent">live</Badge>
        ) : (
          <Badge variant="muted">last run</Badge>
        )}
      </GlassCardHeader>
      <GlassCardContent className="space-y-0">
        {animatedSteps.map((step, i) => (
          <div key={step.id}>
            <PipelineNode
              id={step.id}
              label={step.label}
              caption={step.caption}
              icon={step.icon}
              status={step.status}
              meta={step.meta}
            />
            {i < animatedSteps.length - 1 ? (
              <PipelineConnection
                fromIndex={i}
                toIndex={i + 1}
                // Animate the connector that runs INTO the active node
                // (the one leaving it shows the dot traveling down).
                animated={streaming && i === activeIndex}
              />
            ) : null}
          </div>
        ))}
      </GlassCardContent>
    </GlassCard>
  );
}