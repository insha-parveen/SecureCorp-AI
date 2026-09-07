"use client";

// DemoAccessBadge — the top-nav pill that makes the demo session legible:
//
//   🔐 Demo admin · 203/276 docs
//
// Three jobs in one popover, all driven by REAL values:
//   1. Says plainly that this is a demo identity (not a real signup).
//   2. Shows how much of the corpus this identity may actually see, counted
//      server-side by the same AuthorizationEngine the retrieval path uses
//      (GET /api/auth/access-summary). No role — not even `admin` — gets a
//      superuser bypass, which is why the number is never the full corpus.
//   3. Lets you switch identity in place ("Try another role") so the effect of
//      RBAC/ABAC on retrieval is something you can feel, not just read about.
//
// It also carries the key-findings note explaining that enforcing authorization
// legitimately LOWERS measured retrieval scores — context that otherwise makes
// the evaluation numbers look worse than the system is.

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Popover from "@radix-ui/react-popover";
import { Info, Lock, ShieldCheck } from "lucide-react";
import { accessSummary, listDemoUsers, login } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";

export function DemoAccessBadge() {
  const queryClient = useQueryClient();
  const { user, setUser } = useCurrentUser();

  const { data: summary } = useQuery({
    queryKey: ["access-summary", user?.user_id],
    queryFn: accessSummary,
    enabled: user !== null,
    staleTime: 60_000,
  });

  const { data: demoUsers } = useQuery({
    queryKey: ["demo-users"],
    queryFn: listDemoUsers,
    staleTime: Infinity,
  });

  // Switching identity re-issues the cookie; no logout round-trip needed.
  // We deliberately do NOT clear the whole cache (that would evict the demo
  // user list); we invalidate only what is scoped to the identity.
  const switchRole = useMutation({
    mutationFn: (userId: string) => login(userId),
    onSuccess: (next) => {
      setUser(next);
      queryClient.setQueryData(["me"], next);
      queryClient.invalidateQueries({ queryKey: ["access-summary"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  if (!user) return null;

  const others = (demoUsers?.users ?? []).filter((u) => u.user_id !== user.user_id);
  // Only claim a document count once the server has actually reported one.
  const hasCounts = summary?.available === true && summary.total_documents > 0;

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Demo session and access scope"
          className="hidden items-center gap-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-card)]/50 px-2.5 py-1 text-[11px] text-[var(--color-muted-foreground)] transition-colors hover:bg-[var(--color-card)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] md:flex"
        >
          <Lock size={11} aria-hidden />
          <span className="font-medium text-[var(--color-foreground)]">
            Demo {user.user_id}
          </span>
          {hasCounts ? (
            <>
              <span aria-hidden>·</span>
              <span className="font-mono tabular-nums">
                {summary.accessible_documents}/{summary.total_documents} docs
              </span>
            </>
          ) : null}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-40 max-h-[80vh] w-80 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3 text-[var(--color-card-foreground)] shadow-[0_12px_32px_-12px_rgb(0_0_0_/_0.6)] backdrop-blur-md"
        >
          <div className="flex items-center gap-2 pb-2">
            <ShieldCheck size={14} className="text-[var(--color-success)]" aria-hidden />
            <p className="text-sm font-medium">Demo session</p>
          </div>

          <p className="pb-3 text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
            Signed in as a fictional NexaCore identity over synthetic data. Roles
            come from the server-verified JWT — never from the browser.
          </p>

          {/* Access scope — live authorization result. */}
          {hasCounts ? (
            <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-muted)]/30 p-2.5">
              <p className="font-mono text-sm tabular-nums">
                {summary.accessible_documents} of {summary.total_documents} documents
              </p>
              <p className="font-mono text-[11px] text-[var(--color-muted-foreground)] tabular-nums">
                {summary.accessible_chunks} of {summary.total_chunks} chunks retrievable
              </p>
              <p className="mt-1.5 text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
                Counted by the same authorization check the retrieval path runs.
                No role — including <span className="font-mono">admin</span> — gets
                a superuser bypass, so nobody sees the whole corpus.
              </p>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-1 py-3">
            {user.roles.map((role) => (
              <Badge key={role} variant="muted">
                {role}
              </Badge>
            ))}
            {user.department ? <Badge variant="muted">{user.department}</Badge> : null}
          </div>

          <div className="h-px bg-[var(--color-border)]" />

          {/* Key findings — the honest caveat about what authorization costs. */}
          <div className="py-3">
            <p className="flex items-center gap-1.5 pb-1.5 text-[11px] font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]">
              <Info size={11} aria-hidden />
              Key findings
            </p>
            <ul className="space-y-1.5 text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
              <li>
                <span className="text-[var(--color-foreground)]">
                  Security lowers measured recall — by design.
                </span>{" "}
                Evaluation runs through the authorized path, so documents the eval
                identity may not read count as misses. Raw retrieval scores higher
                than the numbers we publish; we publish the enforced ones.
              </li>
              <li>
                <span className="text-[var(--color-foreground)]">
                  Zero unauthorized chunks reach the model.
                </span>{" "}
                Enforced at the data boundary and covered by a regression test —
                cache reuse is scope-hashed, with no cross-tenant, cross-role or
                cross-department leakage.
              </li>
              <li>
                <span className="text-[var(--color-foreground)]">
                  Filter placement matters more than filter strength.
                </span>{" "}
                A narrow pre-filter on the vector index cost a large share of dense
                recall while adding no security, because the post-filter was already
                the real boundary.
              </li>
            </ul>
          </div>

          {others.length > 0 ? (
            <>
              <div className="h-px bg-[var(--color-border)]" />
              <div className="pt-3">
                <p className="pb-1.5 text-[11px] font-medium uppercase tracking-wide text-[var(--color-muted-foreground)]">
                  Try another role
                </p>
                <div className="flex flex-col gap-1">
                  {others.map((u) => (
                    <button
                      key={u.user_id}
                      type="button"
                      onClick={() => switchRole.mutate(u.user_id)}
                      disabled={switchRole.isPending}
                      className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-[12px] transition-colors hover:bg-[var(--color-accent)] disabled:opacity-50"
                    >
                      <span className="font-medium">{u.user_id}</span>
                      <span className="truncate font-mono text-[10px] text-[var(--color-muted-foreground)]">
                        {u.roles.join(", ")}
                      </span>
                    </button>
                  ))}
                </div>
                <p className="pt-1.5 text-[10px] text-[var(--color-muted-foreground)]">
                  Switching re-issues the session cookie and re-runs the access
                  count — ask the same question again to see the difference.
                </p>
              </div>
            </>
          ) : null}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
