"use client";

// shadcn Button primitive. Adapted for Tailwind v4 + the project's
// design tokens. Only the variants we actually use are exposed.

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] hover:opacity-90",
        ghost: "hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]",
        outline:
          "border border-[var(--color-border)] bg-transparent hover:bg-[var(--color-accent)]",
        destructive:
          "bg-[var(--color-destructive)] text-[var(--color-destructive-foreground)] hover:opacity-90",
        // Login Sign In CTA only. Uses the accent-violet → primary → series-2
        // gradient that mirrors the Logo shield. NOT reused elsewhere —
        // categorical chart colors must not bleed into interactive controls.
        gradient:
          "bg-gradient-to-r from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] text-white shadow-[0_8px_24px_-12px_color-mix(in_oklch,var(--color-accent-violet)_60%,transparent)] hover:opacity-95",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };
