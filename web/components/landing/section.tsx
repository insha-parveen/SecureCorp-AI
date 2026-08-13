"use client";

// Section — the landing page's anchored section wrapper. Each section is a
// scroll target (id) with a numbered eyebrow. The number is NOT decoration:
// 01–04 are the real request sequence (path → retrieval → security →
// evidence), so the numbering encodes the order a query actually flows
// through the system. The eyebrow number is set in the display face; the
// kicker word in mono so it reads as a stage label.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SectionProps {
  /** DOM id used as the scroll-spy anchor and nav target. */
  id: string;
  /** Zero-padded stage number, e.g. "01". */
  index: string;
  /** Short stage label, e.g. "The path". */
  kicker: string;
  /** Section heading (display face). */
  title: string;
  /** Optional lead paragraph under the title. */
  lead?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Section({ id, index, kicker, title, lead, children, className }: SectionProps) {
  return (
    <section
      id={id}
      // scroll-mt keeps the sticky topbar from covering the heading when the
      // nav jumps here; outline-none because focus is moved here programmatically
      // by the scroll-spy and the ring would otherwise flash.
      className={cn("scroll-mt-24 outline-none", className)}
      aria-labelledby={`${id}-title`}
    >
      <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
        <div className="mb-8 flex items-baseline gap-4">
          <span
            aria-hidden
            className="font-display text-2xl font-semibold tabular-nums text-[var(--color-primary)]/70"
          >
            {index}
          </span>
          <div className="flex flex-col gap-1">
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-muted-foreground)]">
              {kicker}
            </span>
            <h2
              id={`${id}-title`}
              className="font-display text-2xl font-semibold tracking-tight sm:text-3xl"
            >
              {title}
            </h2>
          </div>
        </div>
        {lead ? (
          <p className="mb-10 max-w-2xl text-[15px] leading-relaxed text-[var(--color-muted-foreground)]">
            {lead}
          </p>
        ) : null}
        {children}
      </div>
    </section>
  );
}
