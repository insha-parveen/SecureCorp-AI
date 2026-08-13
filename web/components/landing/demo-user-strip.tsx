"use client";

// DemoUserStrip — a prominent, one-click demo sign-in row for the landing
// page. The demo accounts are the real MVP auth path (CLAUDE.md §24.5); they
// used to be buried behind a disclosure on /login. Here they are surfaced
// directly so a visitor can jump into the assistant as any role immediately.
//
// Reuses the exact contract from LoginForm's demo view: fetch the seeded
// users (listDemoUsers), then login(user_id) → set the user → /chat. No new
// auth surface, no password. If the backend is down, it says so plainly.

import * as React from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listDemoUsers, login } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { RoleBadge } from "@/components/auth/role-badge";
import { cn } from "@/lib/utils";

export function DemoUserStrip({ className }: { className?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setUser } = useCurrentUser();

  const users = useQuery({
    queryKey: ["demo-users"],
    queryFn: listDemoUsers,
    staleTime: 5 * 60 * 1000,
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      setUser(user);
      queryClient.setQueryData(["me"], user);
      router.push("/chat");
    },
  });

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-muted-foreground)]">
        Or sign in instantly as a demo user
      </p>

      {users.isLoading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Loading demo accounts…</p>
      ) : users.error ? (
        <p className="text-sm text-[var(--color-muted-foreground)]" role="status">
          Demo accounts need the backend running on :8000.
        </p>
      ) : (
        <ul className="flex flex-wrap items-center justify-center gap-2">
          {users.data?.users.map((u) => (
            <li key={u.user_id}>
              <button
                type="button"
                onClick={() => loginMutation.mutate(u.user_id)}
                disabled={loginMutation.isPending}
                aria-label={`Sign in as ${u.user_id} (${u.roles.join(", ")})`}
                className={cn(
                  "group flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-card)]/60 py-1.5 pl-3 pr-2 backdrop-blur-md transition-colors",
                  "hover:border-[color-mix(in_oklch,var(--color-primary)_45%,var(--color-border))] hover:bg-[var(--color-card)]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] disabled:opacity-50",
                )}
              >
                <span className="font-mono text-[13px] font-medium text-[var(--color-foreground)]">
                  {u.user_id}
                </span>
                {u.roles[0] ? <RoleBadge role={u.roles[0]} /> : null}
              </button>
            </li>
          ))}
        </ul>
      )}

      {loginMutation.isPending ? (
        <p className="text-xs text-[var(--color-muted-foreground)]" role="status">
          Signing in…
        </p>
      ) : loginMutation.error ? (
        <p className="text-xs text-[var(--color-critical)]" role="alert">
          Sign-in failed. Is the backend running?
        </p>
      ) : null}
    </div>
  );
}
