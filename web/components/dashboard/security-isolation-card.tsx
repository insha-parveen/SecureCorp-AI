"use client";

// SecurityIsolationCard — the four status rows (RBAC, tenant,
// cache-scope, PII) plus an inline-SVG orbiting-shield decoration.
//
// Per §24.1 ("safe substitutions") we replace the reference's 3D
// orbiting shield with a hand-rolled inline SVG that does a slow
// CSS rotate — gives the panel the same visual anchor without a
// 3D dependency, and the rotation collapses under
// prefers-reduced-motion (CSS media query, no JS).

import { CheckCircle2, ShieldAlert, ShieldCheck } from "lucide-react";
import { securityChecks } from "@/lib/mock-data";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

function statusVariant(status: "PASS" | "ACTIVE" | "FAIL"): "success" | "warning" | "critical" {
  if (status === "PASS") return "success";
  if (status === "ACTIVE") return "warning";
  return "critical";
}

function statusIcon(status: "PASS" | "ACTIVE" | "FAIL"): React.ComponentType<{ size?: number }> {
  if (status === "PASS") return ShieldCheck;
  if (status === "ACTIVE") return CheckCircle2;
  return ShieldAlert;
}

export function SecurityIsolationCard() {
  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex flex-col gap-1">
          <GlassCardTitle>Security &amp; isolation</GlassCardTitle>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Live checks on every retrieval path
          </p>
        </div>
        <Badge variant="muted">(Demo data)</Badge>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="flex items-start gap-4">
          {/* Orbit decoration. Pure SVG, slow CSS rotate. */}
          <div
            aria-hidden
            className="relative hidden size-24 shrink-0 place-items-center md:flex"
          >
            <div className="security-orbit absolute inset-0 m-auto size-24">
              <div className="absolute left-1/2 top-0 size-1.5 -translate-x-1/2 rounded-full bg-[var(--color-series-3)] shadow-[0_0_8px_var(--color-series-3)]" />
              <div className="absolute left-0 top-1/2 size-1.5 -translate-y-1/2 rounded-full bg-[var(--color-series-2)] shadow-[0_0_8px_var(--color-series-2)]" />
              <div className="absolute bottom-0 left-1/2 size-1.5 -translate-x-1/2 rounded-full bg-[var(--color-series-1)] shadow-[0_0_8px_var(--color-series-1)]" />
            </div>
            <svg
              viewBox="0 0 32 32"
              className="relative size-10"
              aria-hidden
            >
              <defs>
                <linearGradient id="security-shield" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="var(--color-accent-violet)" />
                  <stop offset="0.5" stopColor="var(--color-primary)" />
                  <stop offset="1" stopColor="var(--color-series-2)" />
                </linearGradient>
              </defs>
              <path
                d="M16 3 L28 7 V16 C28 22 23 27 16 29 C9 27 4 22 4 16 V7 Z"
                stroke="url(#security-shield)"
                strokeWidth="1.6"
                fill="none"
              />
              <path
                d="M11 16 L15 20 L21 12"
                stroke="url(#security-shield)"
                strokeWidth="1.6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <ul className="flex-1 divide-y divide-[var(--color-border)]/60">
            {securityChecks.map((check) => {
              const Icon = statusIcon(check.status);
              const variant = statusVariant(check.status);
              return (
                <li
                  key={check.id}
                  className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span
                      className={cn(
                        "inline-flex size-7 shrink-0 items-center justify-center rounded-md",
                        variant === "success" &&
                          "bg-[color-mix(in_oklch,var(--color-success)_18%,transparent)] text-[var(--color-success)]",
                        variant === "warning" &&
                          "bg-[color-mix(in_oklch,var(--color-warning)_18%,transparent)] text-[var(--color-warning)]",
                        variant === "critical" &&
                          "bg-[color-mix(in_oklch,var(--color-critical)_18%,transparent)] text-[var(--color-critical)]",
                      )}
                    >
                      <Icon size={14} />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{check.label}</p>
                      <p className="truncate text-[11px] text-[var(--color-muted-foreground)]">
                        {check.detail}
                      </p>
                    </div>
                  </div>
                  <Badge variant={variant}>{check.status}</Badge>
                </li>
              );
            })}
          </ul>
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}