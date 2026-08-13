"use client";

// PipelineNode — a single tile in the vertical pipeline chain. Icon
// chip on the left, label + caption + optional meta on the right.
//
// Visual states map to the data-viz status colors:
//   - done    → muted-foreground text, --success tint on the icon
//   - active  → primary accent on the icon + ring, glow halo
//   - pending → muted-foreground, low opacity
//
// Per the data-viz skill, status is communicated via the icon's
// color, not the text color (text stays in primary-foreground).

import * as React from "react";
import * as Lucide from "lucide-react";
import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PipelineNodeProps {
  id: string;
  label: string;
  caption: string;
  /** Lucide icon name (e.g., "MessageSquare"). */
  icon: string;
  status: "done" | "active" | "pending";
  /** Optional 1-2 line subtitle (e.g., "Top 50 results"). */
  meta?: string;
}

export function PipelineNode({
  label,
  caption,
  icon,
  status,
  meta,
}: PipelineNodeProps) {
  const Icon = resolveIcon(icon);

  return (
    <div
      aria-current={status === "active" ? "step" : undefined}
      data-pipeline-status={status}
      className={cn(
        "flex items-start gap-3 rounded-md border px-3 py-2 transition-colors",
        status === "active" &&
          "border-[var(--color-primary)] bg-[color-mix(in_oklch,var(--color-primary)_8%,transparent)] shadow-[0_0_0_1px_color-mix(in_oklch,var(--color-primary)_20%,transparent)]",
        status === "done" &&
          "border-[var(--color-border)] bg-[var(--color-card)]/40",
        status === "pending" && "border-dashed border-[var(--color-border)] bg-transparent opacity-60",
      )}
    >
      <span
        aria-hidden
        className={cn(
          "grid size-8 shrink-0 place-items-center rounded-md border",
          status === "active" &&
            "border-[var(--color-primary)] text-[var(--color-primary)] bg-[color-mix(in_oklch,var(--color-primary)_14%,transparent)]",
          status === "done" &&
            "border-[var(--color-success)] text-[var(--color-success)] bg-[color-mix(in_oklch,var(--color-success)_14%,transparent)]",
          status === "pending" &&
            "border-[var(--color-border)] text-[var(--color-muted-foreground)] bg-[var(--color-card)]/40",
        )}
      >
        {status === "done" ? <CheckCircle2 size={14} /> : <Icon size={14} />}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span
            className={cn(
              "truncate text-sm font-medium",
              status === "pending" && "text-[var(--color-muted-foreground)]",
            )}
          >
            {label}
          </span>
          {status === "active" ? (
            <span
              aria-hidden
              className="inline-block size-1.5 rounded-full bg-[var(--color-primary)] shadow-[0_0_6px_var(--color-primary)]"
            />
          ) : null}
        </div>
        <p className="truncate text-[11px] text-[var(--color-muted-foreground)]">
          {caption}
        </p>
        {meta ? (
          <p className="mt-0.5 truncate font-mono text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
            {meta}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function resolveIcon(name: string): React.ComponentType<{ size?: number; strokeWidth?: number }> {
  // Lucide's barrel has every icon we need; fall back to a circle if
  // the name doesn't resolve.
  const lib = Lucide as unknown as Record<
    string,
    React.ComponentType<{ size?: number; strokeWidth?: number }>
  >;
  return lib[name] ?? Lucide.Circle;
}