"use client";

// /settings — account settings placeholder. Per §24.8 light-mode
// toggle and theme persistence are deferred, so this surface is a
// thin account + privacy panel at MVP.

import { PageHeader } from "@/components/layout/page-header";
import { UserContextCard } from "@/components/dashboard/user-context-card";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" eyebrow="Account" />
      <div className="space-y-6 p-4 sm:p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Account</GlassCardTitle>
              </GlassCardHeader>
              <GlassCardContent className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">Display name</p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">
                      Mirrors your <code className="font-mono text-[11px]">user_id</code> from the JWT.
                    </p>
                  </div>
                  <Badge variant="muted">Read-only at MVP</Badge>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">Email</p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">
                      Derived from your work email prefix.
                    </p>
                  </div>
                  <Badge variant="muted">Read-only at MVP</Badge>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">Theme</p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">
                      Dark mode is the default; light mode is deferred.
                    </p>
                  </div>
                  <Badge variant="muted">Dark (only)</Badge>
                </div>
              </GlassCardContent>
            </GlassCard>

            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Session</GlassCardTitle>
              </GlassCardHeader>
              <GlassCardContent className="space-y-3">
                <p className="text-xs text-[var(--color-muted-foreground)]">
                  JWT cookie is httpOnly and scoped to <code className="font-mono text-[11px]">Domain=localhost</code>.
                  Sign out invalidates the cookie server-side.
                </p>
                <Button variant="outline" size="sm" disabled>
                  Revoke all sessions (deferred)
                </Button>
              </GlassCardContent>
            </GlassCard>
          </div>

          <aside className="lg:sticky lg:top-20 lg:self-start">
            <UserContextCard />
          </aside>
        </div>
      </div>
    </>
  );
}