"use client";

// UserMenu — the avatar + popover that carries session identity and the
// account actions (Settings, Sign out) in the top nav. Consolidates what used
// to be spread across the sidebar user card and the /chat TopBar: one place
// owns the logout mutation now.
//
// Built on Radix Popover (already used by citation-hover-card.tsx) rather than
// a dropdown-menu dep we don't have. The avatar gradient mirrors the old
// sidebar avatar so the visual identity carries over.

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as Popover from "@radix-ui/react-popover";
import { LogOut, Settings as SettingsIcon } from "lucide-react";
import { logout } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, setUser } = useCurrentUser();

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      setUser(null);
      queryClient.clear();
      router.push("/login");
    },
  });

  if (!user) return null;

  const initials = user.user_id.slice(0, 2);

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Account menu"
          className="flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-card)]/50 py-1 pl-1 pr-2.5 transition-colors hover:bg-[var(--color-card)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] text-[11px] font-semibold uppercase text-white"
          >
            {initials}
          </span>
          <span className="hidden max-w-[8rem] truncate text-sm font-medium sm:inline">
            {user.user_id}
          </span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-40 w-64 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-3 text-[var(--color-card-foreground)] shadow-[0_12px_32px_-12px_rgb(0_0_0_/_0.6)] backdrop-blur-md"
        >
          {/* Identity block */}
          <div className="flex items-center gap-3 pb-3">
            <span
              aria-hidden
              className="grid size-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] text-[13px] font-semibold uppercase text-white"
            >
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user.user_id}</p>
              <p className="truncate text-[11px] text-[var(--color-muted-foreground)]">
                {user.department || "—"} · {user.tenant_id}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1 pb-3">
            {user.roles.map((role) => (
              <Badge key={role} variant="muted">
                {role}
              </Badge>
            ))}
          </div>

          <div className="h-px bg-[var(--color-border)]" />

          {/* Actions */}
          <div className="pt-2">
            <Popover.Close asChild>
              <Link
                href="/settings"
                className={cn(
                  "flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors",
                  "text-[var(--color-foreground)] hover:bg-[var(--color-accent)]",
                )}
              >
                <SettingsIcon size={15} strokeWidth={2} aria-hidden />
                Settings
              </Link>
            </Popover.Close>
            <button
              type="button"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
              className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm text-[var(--color-foreground)] transition-colors hover:bg-[var(--color-accent)] disabled:opacity-50"
            >
              <LogOut size={15} strokeWidth={2} aria-hidden />
              {logoutMutation.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
