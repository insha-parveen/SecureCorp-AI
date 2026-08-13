"use client";

// Logo — geometric shield with a violet → blue → cyan gradient stroke
// (uses --accent-violet, --primary, --series-2). Used in the sidebar
// header and the login card. Pure inline SVG so it inherits currentColor
// for fills and composes into the gradient via <defs>.

import * as React from "react";
import { cn } from "@/lib/utils";

export interface LogoProps extends React.SVGProps<SVGSVGElement> {
  /** Pixel size of the rendered SVG; width and height share this value. */
  size?: number;
  /** Show the wordmark beside the shield. Default: true. */
  withWordmark?: boolean;
}

const GRADIENT_ID = "securecorp-logo-gradient";

export function Logo({ size = 28, withWordmark = true, className, ...props }: LogoProps) {
  return (
    <span
      className={cn("inline-flex items-center gap-2 font-semibold tracking-tight", className)}
      // We wrap in a span so the wordmark can sit beside the SVG without
      // requiring the consumer to compose two elements.
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="SecureCorp AI"
        role="img"
        {...props}
      >
        <defs>
          <linearGradient id={GRADIENT_ID} x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="var(--color-accent-violet)" />
            <stop offset="0.5" stopColor="var(--color-primary)" />
            <stop offset="1" stopColor="var(--color-series-2)" />
          </linearGradient>
        </defs>
        {/* Shield outline */}
        <path
          d="M16 2 L28 6 V15 C28 22.5 22.5 27.5 16 30 C9.5 27.5 4 22.5 4 15 V6 Z"
          stroke={`url(#${GRADIENT_ID})`}
          strokeWidth="1.6"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Inner geometric mark: a stylized "S" formed by two stacked bars */}
        <path
          d="M11 12 H20 M11 12 V15 H18 M11 20 H21 M21 20 V17 H13"
          stroke={`url(#${GRADIENT_ID})`}
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      {withWordmark ? (
        <span className="text-sm">
          <span className="text-[var(--color-foreground)]">Secure</span>
          <span className="text-[var(--color-primary)]">Corp</span>
          <span className="ml-1 text-[var(--color-muted-foreground)]">AI</span>
        </span>
      ) : null}
    </span>
  );
}