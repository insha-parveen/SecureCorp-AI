"use client";

// /security — per-role access model. The security-isolation panel now lives on
// /analytics (this page is about the authorization MODEL, not live metrics).
// The RBAC matrix is heavy, so it is tucked behind an info (ⓘ) toggle: a
// one-line summary until the user asks for the full table.

import { useState } from "react";
import { ChevronDown, Info } from "lucide-react";
import { useCurrentUser } from "@/lib/auth-context";
import { PageHeader } from "@/components/layout/page-header";
import { SecureCorpPipeline } from "@/components/pipeline/securecorp-pipeline";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RbacCheck {
  role: string;
  accessTo: string;
  blockedFrom: string;
  status: "PASS" | "FAIL";
}

const RBAC_MATRIX: RbacCheck[] = [
  {
    role: "employee",
    accessTo: "General policies · own employee record",
    blockedFrom: "HR-only · other employees' records",
    status: "PASS",
  },
  {
    role: "manager",
    accessTo: "All employee + reports' records",
    blockedFrom: "HR-confidential · cross-team records",
    status: "PASS",
  },
  {
    role: "hr",
    accessTo: "All HR policies + all employee records",
    blockedFrom: "Finance invoices · IT security",
    status: "PASS",
  },
  {
    role: "finance",
    accessTo: "All invoices · expense claims · vendors",
    blockedFrom: "Employee PII · IT incidents",
    status: "PASS",
  },
  {
    role: "it",
    accessTo: "Security policies · IT assets · incidents",
    blockedFrom: "Finance · HR PII",
    status: "PASS",
  },
  {
    role: "admin",
    accessTo: "Full audit log · all RBAC bypasses (audited)",
    blockedFrom: "— (admin bypasses logged)",
    status: "PASS",
  },
];

export default function SecurityPage() {
  const { user } = useCurrentUser();
  const role = user?.roles[0] ?? "—";
  const [rbacOpen, setRbacOpen] = useState(false);

  return (
    <>
      <PageHeader title="Security" eyebrow="Isolation">
        <Badge variant="success">PASS · 0 violations</Badge>
      </PageHeader>
      <div className="space-y-6 p-4 sm:p-6">
        <header className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]/40 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
                Current session
              </p>
              <p className="mt-1 text-sm">
                Role <Badge variant="accent">{role}</Badge> — every request
                is verified server-side before evidence reaches the LLM.
              </p>
            </div>
            <Badge variant="muted">Last 7d</Badge>
          </div>
        </header>

        {/* The actual request pipeline, shown statically. Reinforces that
            authorization runs BEFORE retrieval / SQL / generation. On /chat
            the same component animates live per request. */}
        <SecureCorpPipeline
          user={user}
          title="Request pipeline — authorization before retrieval"
        />

        {/* RBAC matrix — heavy, so collapsed behind an info toggle. */}
        <GlassCard>
          <GlassCardHeader className="flex-row items-center justify-between space-y-0">
            <div className="flex flex-col gap-1">
              <GlassCardTitle>RBAC matrix</GlassCardTitle>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                6 roles · 0 violations · per-role access map (Phase 5)
              </p>
            </div>
            <button
              type="button"
              onClick={() => setRbacOpen((v) => !v)}
              aria-expanded={rbacOpen}
              aria-controls="rbac-matrix-panel"
              className="flex items-center gap-1.5 rounded-md border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-medium text-[var(--color-muted-foreground)] transition-colors hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
            >
              <Info size={13} strokeWidth={2} aria-hidden />
              {rbacOpen ? "Hide details" : "Details"}
              <ChevronDown
                size={13}
                strokeWidth={2}
                aria-hidden
                className={cn("transition-transform", rbacOpen && "rotate-180")}
              />
            </button>
          </GlassCardHeader>
          {rbacOpen ? (
            <GlassCardContent id="rbac-matrix-panel">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="py-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                        Role
                      </th>
                      <th className="py-2 px-2 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                        Access scope
                      </th>
                      <th className="py-2 px-2 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                        Blocked from
                      </th>
                      <th className="py-2 px-2 text-right text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {RBAC_MATRIX.map((row) => (
                      <tr
                        key={row.role}
                        className={`border-b border-[var(--color-border)]/60 last:border-b-0 ${
                          role === row.role
                            ? "bg-[color-mix(in_oklch,var(--color-primary)_6%,transparent)]"
                            : ""
                        }`}
                      >
                        <th scope="row" className="py-2 pr-4 text-left font-medium">
                          {row.role}
                        </th>
                        <td className="py-2 px-2 text-[var(--color-foreground)]">
                          {row.accessTo}
                        </td>
                        <td className="py-2 px-2 text-[var(--color-muted-foreground)]">
                          {row.blockedFrom}
                        </td>
                        <td className="py-2 px-2 text-right">
                          <Badge variant={row.status === "PASS" ? "success" : "critical"}>
                            {row.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCardContent>
          ) : null}
        </GlassCard>
      </div>
    </>
  );
}
