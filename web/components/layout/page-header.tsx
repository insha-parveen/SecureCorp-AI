"use client";

// PageHeader — a compact, NON-sticky title row for dashboard pages. Now that
// navigation lives in the sticky <DashboardTopNav/> and the per-page
// <DashboardTopbar/> is gone, pages keep their heading via this lightweight
// block. It is deliberately not a second sticky bar — just an eyebrow + h1 with
// an optional right-hand slot (badges, actions) — so the surface reads less
// dense than the old two-bar stack.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface PageHeaderProps {
  title: string;
  /** Optional uppercase kicker above the title (e.g., "Performance"). */
  eyebrow?: string;
  /** Optional right-aligned content (badges, actions). */
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, eyebrow, children, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-end justify-between gap-3 border-b border-[var(--color-border)] px-4 py-4 sm:px-6",
        className,
      )}
    >
      <div className="flex flex-col gap-1">
        {eyebrow ? (
          <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-muted-foreground)]">
            {eyebrow}
          </span>
        ) : null}
        <h1 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">{title}</h1>
      </div>
      {children ? <div className="flex items-center gap-2">{children}</div> : null}
    </div>
  );
}
