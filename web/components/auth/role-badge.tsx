"use client";

// Tiny role badge — a pill of the user's roles. Used in the top bar and
// next to login tiles. Not a state surface; purely presentational.

import { cn } from "@/lib/utils";

export function RoleBadge({ role, className }: { role: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-[var(--color-border)] bg-[var(--color-accent)] px-2 py-0.5 text-xs font-medium text-[var(--color-accent-foreground)]",
        className,
      )}
    >
      {role}
    </span>
  );
}
