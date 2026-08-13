"use client";

// AuthzDecisionCard — the small card on the right rail that shows
// "User → Authorization → Allowed" with a PASS / ALLOWED badge. Pure
// presentational; the actual authorization decision is made on the
// server and never exposed in detail on the client.
//
// Layout: three nodes (user, authz, allowed) connected by an inline
// SVG path with a moving dot. Respects prefers-reduced-motion (the
// dot animation collapses via the global override).

import { useCurrentUser } from "@/lib/auth-context";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, KeyRound, User as UserIcon } from "lucide-react";

export function AuthzDecisionCard() {
  const { user } = useCurrentUser();
  const role = user?.roles[0] ?? "user";

  return (
    <GlassCard>
      <GlassCardHeader>
        <GlassCardTitle>Authorization decision</GlassCardTitle>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="flex items-center gap-2">
          <Node icon={UserIcon} label="User" sublabel={role} />
          <Connector />
          <Node
            icon={KeyRound}
            label="Authorization"
            sublabel="RBAC + ABAC"
            emphasized
          />
          <Connector />
          <Node
            icon={CheckCircle2}
            label="Allowed"
            sublabel="scope match"
            success
          />
        </div>
        <p className="mt-3 text-[11px] text-[var(--color-muted-foreground)]">
          Verified server-side on every request. The client cannot
          override this scope.
        </p>
        <div className="mt-2 flex justify-end">
          <Badge variant="success">PASS · ALLOWED</Badge>
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}

interface NodeProps {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  sublabel: string;
  emphasized?: boolean;
  success?: boolean;
}

function Node({ icon: Icon, label, sublabel, emphasized, success }: NodeProps) {
  const ringClass = success
    ? "border-[var(--color-success)] text-[var(--color-success)]"
    : emphasized
      ? "border-[var(--color-primary)] text-[var(--color-primary)]"
      : "border-[var(--color-border)] text-[var(--color-muted-foreground)]";
  return (
    <div className="flex min-w-0 flex-1 flex-col items-center gap-1 text-center">
      <span
        className={`grid size-9 place-items-center rounded-md border bg-[var(--color-card)]/40 ${ringClass}`}
      >
        <Icon size={14} />
      </span>
      <span className="truncate text-[11px] font-semibold">{label}</span>
      <span className="truncate text-[10px] text-[var(--color-muted-foreground)]">
        {sublabel}
      </span>
    </div>
  );
}

function Connector() {
  // Short SVG line with a subtle dot. The dot animation is handled by
  // the .authz-dot CSS class — it collapses under prefers-reduced-motion.
  return (
    <svg
      viewBox="0 0 24 8"
      className="h-2 flex-1"
      aria-hidden
    >
      <line
        x1="0"
        y1="4"
        x2="24"
        y2="4"
        stroke="var(--color-border)"
        strokeWidth="1"
        strokeDasharray="2 2"
      />
      <circle cx="6" cy="4" r="1.6" fill="var(--color-primary)" className="authz-dot" />
    </svg>
  );
}