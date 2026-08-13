"use client";

// SecureCorpPipelineNode — a single node in the branching SecureCorp
// pipeline graph. Distinct from the legacy `pipeline-node.tsx` (which the
// dashboard's linear PipelineFlow still uses): this one models the full
// 4-state machine (idle | processing | completed | failed) and carries a
// route-family accent color.
//
// Color families (CLAUDE.md §26.2) — reuse existing tokens, never raw hex:
//   rag        -> --color-success       (green)
//   sql        -> --color-series-1      (blue)
//   refuse     -> --color-critical      (red)
//   generation -> --color-accent-violet (purple)
//   neutral    -> --color-primary       (the spine: user/auth/authz/router/response)
//
// Status is communicated by BOTH color and an icon/aria label, so the
// flow is legible without animation and to screen readers.

import * as React from "react";
import * as Lucide from "lucide-react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NodeStatus } from "@/lib/pipeline-state";

export type NodeAccent = "rag" | "sql" | "refuse" | "generation" | "neutral";

const ACCENT_VAR: Record<NodeAccent, string> = {
  rag: "var(--color-success)",
  sql: "var(--color-series-1)",
  refuse: "var(--color-critical)",
  generation: "var(--color-accent-violet)",
  neutral: "var(--color-primary)",
};

export interface SecureCorpPipelineNodeProps {
  label: string;
  /** 1-3 short lines shown under the label (e.g. "BM25 + Dense"). */
  lines?: string[];
  /** lucide icon name. */
  icon: string;
  status: NodeStatus;
  accent: NodeAccent;
  /** Whether this node opens a detail popover on activate. */
  onActivate?: () => void;
  /** True when its detail popover is open (for aria-expanded). */
  expanded?: boolean;
  className?: string;
}

const STATUS_LABEL: Record<NodeStatus, string> = {
  idle: "idle",
  processing: "processing",
  completed: "completed",
  failed: "failed",
};

export function SecureCorpPipelineNode({
  label,
  lines = [],
  icon,
  status,
  accent,
  onActivate,
  expanded,
  className,
}: SecureCorpPipelineNodeProps) {
  const Icon = resolveIcon(icon);
  const accentVar = ACCENT_VAR[accent];

  // Interactive nodes are buttons (keyboard + screen-reader accessible);
  // non-interactive ones are plain divs.
  const Wrapper = onActivate ? "button" : "div";

  // Accent-dependent styling is built as plain inline style strings from
  // the real token (e.g. "var(--color-success)"). No custom-property
  // indirection — keeps it fully type-safe and avoids Tailwind arbitrary
  // classes that reference a runtime-injected variable.
  const mix = (pct: number) => `color-mix(in oklch, ${accentVar} ${pct}%, transparent)`;
  const wrapperStyle: React.CSSProperties =
    status === "processing"
      ? { borderColor: mix(55), backgroundColor: mix(8), boxShadow: `0 0 16px -4px ${accentVar}` }
      : status === "completed"
        ? { borderColor: mix(35), backgroundColor: mix(8) }
        : {};

  return (
    <Wrapper
      type={onActivate ? "button" : undefined}
      onClick={onActivate}
      aria-expanded={onActivate ? Boolean(expanded) : undefined}
      aria-label={`${label} — ${STATUS_LABEL[status]}`}
      data-status={status}
      className={cn(
        "group relative flex w-full items-start gap-2.5 rounded-lg border px-3 py-2 text-left transition-colors",
        "min-w-[9.5rem] max-w-[13rem]",
        onActivate &&
          "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
        status === "idle" && "border-dashed border-[var(--color-border)] bg-transparent opacity-55",
        status === "failed" &&
          "border-[var(--color-critical)] bg-[color-mix(in_oklch,var(--color-critical)_10%,transparent)]",
        className,
      )}
      style={wrapperStyle}
    >
      <span
        aria-hidden
        className={cn(
          "grid size-7 shrink-0 place-items-center rounded-md border",
          status === "idle" && "border-[var(--color-border)] text-[var(--color-muted-foreground)]",
        )}
        style={status !== "idle" ? { color: accentVar, borderColor: mix(40) } : undefined}
      >
        {status === "completed" ? (
          <CheckCircle2 size={14} />
        ) : status === "failed" ? (
          <XCircle size={14} />
        ) : status === "processing" ? (
          <Loader2 size={14} className="motion-safe:animate-spin" />
        ) : (
          <Icon size={14} />
        )}
      </span>
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block truncate text-[13px] font-medium",
            status === "idle" && "text-[var(--color-muted-foreground)]",
          )}
        >
          {label}
        </span>
        {lines.map((l) => (
          <span
            key={l}
            className="block truncate font-mono text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]"
          >
            {l}
          </span>
        ))}
      </span>
    </Wrapper>
  );
}

function resolveIcon(name: string): React.ComponentType<{ size?: number; className?: string }> {
  const lib = Lucide as unknown as Record<
    string,
    React.ComponentType<{ size?: number; className?: string }>
  >;
  return lib[name] ?? Lucide.Circle;
}
