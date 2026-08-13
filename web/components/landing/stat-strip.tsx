"use client";

// StatStrip — a thin band of the corpus's real, measured scale (CLAUDE.md
// §9b). Big mono numerals so the numbers read as measurements, not marketing.
// Every value carries its source; nothing here is estimated or aggregated.

import * as React from "react";
import { CORPUS_STATS } from "@/lib/landing-facts";

export function StatStrip() {
  return (
    <section aria-label="Corpus scale" className="border-y border-[var(--color-border)] bg-[var(--color-card)]/30">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px px-6 sm:grid-cols-4">
        {CORPUS_STATS.map((stat) => (
          <div key={stat.label} className="flex flex-col gap-1 py-8 sm:py-10">
            <span className="font-mono text-3xl font-semibold tabular-nums tracking-tight text-[var(--color-foreground)] sm:text-4xl">
              {stat.value}
            </span>
            <span className="text-sm text-[var(--color-foreground)]">{stat.label}</span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
              {stat.source}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
