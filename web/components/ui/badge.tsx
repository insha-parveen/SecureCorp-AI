"use client";

// Badge — small status pill. Variants are limited to **semantic** roles
// (success / warning / critical / muted / accent). NEVER reused as
// "series 4" color; categorical chart colors stay reserved for chart
// series identity per the data-viz rule "status colors reserved".

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium leading-none",
  {
    variants: {
      variant: {
        success:
          "bg-[color-mix(in_oklch,var(--color-success)_18%,transparent)] text-[var(--color-success)] ring-1 ring-[color-mix(in_oklch,var(--color-success)_30%,transparent)]",
        warning:
          "bg-[color-mix(in_oklch,var(--color-warning)_18%,transparent)] text-[var(--color-warning)] ring-1 ring-[color-mix(in_oklch,var(--color-warning)_30%,transparent)]",
        critical:
          "bg-[color-mix(in_oklch,var(--color-critical)_18%,transparent)] text-[var(--color-critical)] ring-1 ring-[color-mix(in_oklch,var(--color-critical)_30%,transparent)]",
        accent:
          "bg-[color-mix(in_oklch,var(--color-accent-violet)_18%,transparent)] text-[var(--color-accent-violet)] ring-1 ring-[color-mix(in_oklch,var(--color-accent-violet)_30%,transparent)]",
        muted:
          "bg-[var(--color-muted)] text-[var(--color-muted-foreground)] ring-1 ring-[var(--color-border)]",
      },
    },
    defaultVariants: { variant: "muted" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}