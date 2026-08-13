"use client";

// TraceCard — the landing page's signature element (CLAUDE.md §26 trace
// motif, "disciplined"). It renders like a line of the system's own request
// trace: a labeled header bar, then aligned `key = value` telemetry rows in
// the mono face. Values are colored ONLY by semantic role using existing
// tokens (route, cache tier, authz verdict, resolved citations) — no new hex,
// no chart-series colors bleeding into UI.
//
// This is presentation of REAL observed values (see lib/landing-facts.ts);
// the header label always states the values are from an example request, so
// nothing reads as an aggregate benchmark.

import * as React from "react";
import { cn } from "@/lib/utils";

export type TraceTone = "route-rag" | "route-sql" | "refuse" | "pass" | "muted" | "value";

const toneClass: Record<TraceTone, string> = {
  "route-rag": "text-[var(--color-success)]",
  "route-sql": "text-[var(--color-series-1)]",
  refuse: "text-[var(--color-critical)]",
  pass: "text-[var(--color-success)]",
  muted: "text-[var(--color-muted-foreground)]",
  value: "text-[var(--color-foreground)]",
};

export interface TraceLine {
  key: string;
  value: string;
  tone?: TraceTone;
  /** Optional trailing check mark for "resolved / verified" lines. */
  ok?: boolean;
}

export interface TraceCardProps {
  /** Small label in the header bar, e.g. "example request". */
  label: string;
  /** The prompt line, rendered with a leading `>` like a shell echo. */
  prompt?: string;
  lines: TraceLine[];
  /** Optional footer note (e.g. the source citation). */
  footer?: string;
  className?: string;
}

export function TraceCard({ label, prompt, lines, footer, className }: TraceCardProps) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-[var(--color-border)]",
        // Reads darker than a GlassCard for the terminal feel. Uses the
        // proven opacity-on-a-plain-var pattern (GlassCard / LoginCard), not a
        // nested color-mix, which the arbitrary-value parser can mishandle.
        "bg-[var(--color-background)]/80 backdrop-blur-md",
        "font-mono text-[13px] leading-relaxed",
        "shadow-[inset_0_1px_0_0_rgb(255_255_255_/_0.04),0_24px_60px_-40px_rgb(0_0_0_/_0.7)]",
        className,
      )}
    >
      {/* Header bar: three "window" dots + the label. Reinforces the console
          framing without pretending to be an OS window chrome. */}
      <div className="flex items-center gap-2 border-b border-[var(--color-border)] bg-[var(--color-muted)]/40 px-3 py-2">
        <span className="flex gap-1.5" aria-hidden>
          <span className="size-2 rounded-full bg-[var(--color-critical)]/70" />
          <span className="size-2 rounded-full bg-[var(--color-warning)]/70" />
          <span className="size-2 rounded-full bg-[var(--color-success)]/70" />
        </span>
        <span className="text-[11px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
          {label}
        </span>
      </div>

      <div className="space-y-1.5 px-4 py-3">
        {prompt ? (
          <p className="mb-2 text-[var(--color-foreground)]">
            <span className="mr-1.5 text-[var(--color-primary)]">&gt;</span>
            {prompt}
          </p>
        ) : null}
        {lines.map((line) => (
          <div key={line.key} className="flex items-baseline gap-3">
            <span className="w-20 shrink-0 text-[var(--color-muted-foreground)]">{line.key}</span>
            <span className="text-[var(--color-muted-foreground)]">=</span>
            <span className={cn("font-medium", toneClass[line.tone ?? "value"])}>
              {line.value}
              {line.ok ? <span className="ml-1.5 text-[var(--color-success)]">✓</span> : null}
            </span>
          </div>
        ))}
      </div>

      {footer ? (
        <div className="border-t border-[var(--color-border)] px-4 py-2 text-[11px] text-[var(--color-muted-foreground)]">
          {footer}
        </div>
      ) : null}
    </div>
  );
}
