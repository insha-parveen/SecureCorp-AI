"use client";

// GlassCard — the dashboard's panel primitive. Thin hairline border,
// translucent card surface, soft backdrop blur. Used by every panel on
// /dashboard, /analytics, /security, etc. — never replace this with a
// raw div with similar classes, the four corner cards on a panel grid
// need to render consistently.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** When true, renders an inner glow ring on hover. Used by interactive panels. */
  interactive?: boolean;
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, interactive = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]/60 backdrop-blur-md",
        "text-[var(--color-card-foreground)] shadow-[inset_0_1px_0_0_rgb(255_255_255_/_0.04)]",
        interactive &&
          "transition-shadow hover:shadow-[0_0_0_1px_var(--color-border),0_8px_24px_-12px_rgb(0_0_0_/_0.5),inset_0_1px_0_0_rgb(255_255_255_/_0.06)]",
        className,
      )}
      {...props}
    />
  ),
);
GlassCard.displayName = "GlassCard";

export function GlassCardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1 p-4 pb-2", className)} {...props} />;
}

export function GlassCardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]",
        className,
      )}
      {...props}
    />
  );
}

export function GlassCardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4 pt-2", className)} {...props} />;
}