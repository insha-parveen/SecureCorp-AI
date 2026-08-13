"use client";

// UserContextCard — the small card on the right rail showing the
// authenticated user (initials + name + role + tenant + department +
// clearance + access scope). Hydrated from the live /api/auth/me
// cookie when present; falls back to the mock currentUserContext so
// the dashboard renders before that fetch resolves.
//
// Per §24.5 the JWT is the only source of truth for identity; this
// card is purely presentational and never lets the client override
// the scope that came from the server.

import { useCurrentUser } from "@/lib/auth-context";
import { currentUserContext } from "@/lib/mock-data";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

export function UserContextCard() {
  const { user } = useCurrentUser();

  // Prefer the live user from the verified JWT cookie; fall back to
  // the mock. The dashboard renders both with the same shape so the
  // layout doesn't reflow when the live fetch resolves.
  const initials =
    user?.user_id.slice(0, 2).toUpperCase() ?? currentUserContext.initials;
  const name = user?.user_id ?? currentUserContext.name;
  const role = user?.roles[0] ?? currentUserContext.role;
  const tenant = user?.tenant_id ?? currentUserContext.tenant;
  const department = user?.department ?? currentUserContext.department;
  const clearance = currentUserContext.clearanceLevel;
  const scope = currentUserContext.accessScope;

  return (
    <GlassCard>
      <GlassCardHeader>
        <GlassCardTitle>Active user</GlassCardTitle>
      </GlassCardHeader>
      <GlassCardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <div
            aria-hidden
            className="grid size-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] text-sm font-semibold uppercase text-white"
          >
            {initials}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{name}</p>
            <p className="truncate text-xs text-[var(--color-muted-foreground)]">
              {role} · {tenant}
            </p>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <dt className="font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
              Department
            </dt>
            <dd className="mt-0.5 text-sm">{department}</dd>
          </div>
          <div>
            <dt className="font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
              Clearance
            </dt>
            <dd className="mt-0.5 text-sm">{clearance}</dd>
          </div>
          <div className="col-span-2">
            <dt className="font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
              Access scope
            </dt>
            <dd className="mt-0.5 flex items-center gap-2 text-sm">
              {scope}
              <Badge variant="accent">{role}</Badge>
            </dd>
          </div>
        </dl>
      </GlassCardContent>
    </GlassCard>
  );
}