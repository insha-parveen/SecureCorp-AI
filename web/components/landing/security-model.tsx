"use client";

// SecurityModel — the security section (CLAUDE.md §11, §5 invariants). Three
// quiet panels: the six application roles, the two-tenant isolation, and the
// core invariant stated as measured (0 unauthorized chunks reach the LLM).
// Kept deliberately restrained — the trace motif's boldness is spent in the
// hero and evidence sections, so this reads as calm, factual assurance.

import * as React from "react";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardTitle,
} from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { ROLES, TENANTS } from "@/lib/landing-facts";

export function SecurityModel() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {/* The invariant — the single most important claim, stated plainly. */}
      <GlassCard className="md:col-span-1">
        <GlassCardHeader>
          <GlassCardTitle>The invariant</GlassCardTitle>
        </GlassCardHeader>
        <GlassCardContent className="space-y-3">
          <p className="font-display text-4xl font-semibold tabular-nums text-[var(--color-success)]">
            0
          </p>
          <p className="text-sm leading-relaxed text-[var(--color-foreground)]">
            unauthorized chunks reach the model context. Authorization is
            enforced at the data-access boundary — before retrieval, SQL, and
            generation — never by trusting the LLM.
          </p>
          <p className="font-mono text-[11px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
            §5 · Architecture invariants
          </p>
        </GlassCardContent>
      </GlassCard>

      {/* Roles — RBAC. */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Role-based access</GlassCardTitle>
        </GlassCardHeader>
        <GlassCardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {ROLES.map((role) => (
              <span
                key={role}
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-muted)]/40 px-2.5 py-1 font-mono text-[12px] text-[var(--color-foreground)]"
              >
                {role}
              </span>
            ))}
          </div>
          <p className="text-[13px] leading-relaxed text-[var(--color-muted-foreground)]">
            Six application roles, plus attribute rules (ownership, manager
            scope) layered on top. A document&rsquo;s <code>allowed_roles</code>{" "}
            and <code>classification</code> travel with every chunk.
          </p>
        </GlassCardContent>
      </GlassCard>

      {/* Tenants — isolation. */}
      <GlassCard>
        <GlassCardHeader className="flex-row items-center justify-between space-y-0">
          <GlassCardTitle>Tenant isolation</GlassCardTitle>
          <Badge variant="success">Enforced</Badge>
        </GlassCardHeader>
        <GlassCardContent className="space-y-3">
          <div className="space-y-2">
            {TENANTS.map((tenant) => (
              <div
                key={tenant}
                className="flex items-center gap-2 font-mono text-[13px] text-[var(--color-foreground)]"
              >
                <span className="size-1.5 rounded-full bg-[var(--color-primary)]" aria-hidden />
                {tenant}
              </div>
            ))}
          </div>
          <p className="text-[13px] leading-relaxed text-[var(--color-muted-foreground)]">
            Every row and chunk carries a <code>tenant_id</code>; the structured
            query path filters on it at the boundary. A query for another
            tenant&rsquo;s record resolves to <span className="font-mono">not found</span>,
            not a leak.
          </p>
        </GlassCardContent>
      </GlassCard>
    </div>
  );
}
