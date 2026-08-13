"use client";

// PipelineDetail — the popover shown when a pipeline node is activated
// (click or keyboard). Renders the real backend values for that stage;
// any field the backend did not provide reads "Not available" in a muted
// style, so the panel never implies data it doesn't have.

import * as React from "react";
import { X } from "lucide-react";
import { NOT_AVAILABLE, type NodeDetail } from "@/lib/pipeline-state";
import { cn } from "@/lib/utils";

export interface PipelineDetailProps {
  detail: NodeDetail;
  onClose: () => void;
  /** id used to wire aria-controls / labelledby from the node button. */
  id?: string;
  className?: string;
}

export function PipelineDetail({ detail, onClose, id, className }: PipelineDetailProps) {
  const headingId = id ? `${id}-title` : undefined;
  const ref = React.useRef<HTMLDivElement | null>(null);

  // Close on Escape; focus the panel on open for keyboard users.
  React.useEffect(() => {
    ref.current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      ref={ref}
      id={id}
      role="dialog"
      aria-modal="false"
      aria-labelledby={headingId}
      tabIndex={-1}
      className={cn(
        "z-20 w-64 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3 shadow-[0_12px_32px_-12px_rgb(0_0_0_/_0.6)] backdrop-blur-md focus-visible:outline-none",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 id={headingId} className="text-sm font-semibold text-[var(--color-card-foreground)]">
          {detail.title}
        </h4>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="rounded p-0.5 text-[var(--color-muted-foreground)] hover:text-[var(--color-card-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
        >
          <X size={14} />
        </button>
      </div>
      <p className="mt-1 text-[11px] leading-snug text-[var(--color-muted-foreground)]">
        {detail.description}
      </p>
      <dl className="mt-3 space-y-1.5">
        {detail.rows.map((row) => {
          const unavailable = row.value === NOT_AVAILABLE;
          return (
            <div key={row.label} className="flex items-baseline justify-between gap-3">
              <dt className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                {row.label}
              </dt>
              <dd
                className={cn(
                  "text-right font-mono text-[11px]",
                  unavailable
                    ? "italic text-[var(--color-muted-foreground)] opacity-70"
                    : "text-[var(--color-card-foreground)]",
                )}
              >
                {row.value}
              </dd>
            </div>
          );
        })}
      </dl>
    </div>
  );
}
