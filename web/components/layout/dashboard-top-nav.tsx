"use client";

// DashboardTopNav — the single navigation chrome for the authenticated app,
// replacing both the old left SidebarNav and the per-page DashboardTopbar. It
// is the only sticky bar; pages render a lightweight <PageHeader/> below it.
//
// Desktop (md+): logo · horizontal links · UserMenu.
// Mobile (<md): logo · UserMenu · hamburger → a Radix Dialog slide-in drawer
// with the same links. Radix Dialog (an installed-but-previously-unused dep)
// gives us a focus trap, Escape-to-close, and scroll lock for free.

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { BarChart3, BookOpen, Menu, MessageSquare, Shield, X } from "lucide-react";
import { useCurrentUser } from "@/lib/auth-context";
import { Logo } from "@/components/ui/logo";
import { Badge } from "@/components/ui/badge";
import { UserMenu } from "@/components/layout/user-menu";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
}

// Primary destinations. Chat is home. (Users & Roles removed; Settings lives
// in the UserMenu.)
const NAV_ITEMS: NavItem[] = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/security", label: "Security", icon: Shield },
];

// Exact match OR prefix-with-slash — same rule the old sidebar used so nested
// routes keep their parent lit.
function useIsActive() {
  const pathname = usePathname();
  return React.useCallback(
    (href: string) => pathname === href || pathname?.startsWith(`${href}/`),
    [pathname],
  );
}

export function DashboardTopNav() {
  const isActive = useIsActive();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const pathname = usePathname();

  // Close the mobile drawer on navigation.
  React.useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 backdrop-blur-lg">
      <div className="flex h-14 items-center justify-between gap-4 px-4 sm:px-6">
        {/* Left: brand → chat home */}
        <Link
          href="/chat"
          className="shrink-0 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
          aria-label="SecureCorp AI — go to chat"
        >
          <Logo size={26} />
        </Link>

        {/* Center: desktop links */}
        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
                  active
                    ? "bg-[var(--color-accent)] text-[var(--color-foreground)]"
                    : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)]",
                )}
              >
                <Icon size={15} strokeWidth={2} aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: user menu (desktop + mobile) + mobile hamburger */}
        <div className="flex items-center gap-2">
          <UserMenu />
          <MobileNav
            open={mobileOpen}
            onOpenChange={setMobileOpen}
            items={NAV_ITEMS}
            isActive={isActive}
          />
        </div>
      </div>
    </header>
  );
}

// Mobile drawer — hamburger trigger + Radix Dialog panel sliding from the left.
function MobileNav({
  open,
  onOpenChange,
  items,
  isActive,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  items: NavItem[];
  isActive: (href: string) => boolean | undefined;
}) {
  const { user } = useCurrentUser();

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label="Open navigation menu"
          className="grid size-9 place-items-center rounded-md border border-[var(--color-border)] text-[var(--color-foreground)] transition-colors hover:bg-[var(--color-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] md:hidden"
        >
          <Menu size={18} strokeWidth={2} aria-hidden />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content
          className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-[var(--color-border)] bg-[var(--color-background)] p-4 shadow-2xl focus:outline-none"
          aria-label="Navigation"
        >
          <div className="flex items-center justify-between">
            <Logo size={26} />
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close navigation menu"
                className="grid size-9 place-items-center rounded-md text-[var(--color-muted-foreground)] transition-colors hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
              >
                <X size={18} strokeWidth={2} aria-hidden />
              </button>
            </Dialog.Close>
          </div>

          <Dialog.Title className="sr-only">Navigation</Dialog.Title>

          <nav aria-label="Primary" className="mt-6 flex flex-col gap-1">
            {items.map((item) => {
              const active = isActive(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-[var(--color-accent)] text-[var(--color-foreground)]"
                      : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)]",
                  )}
                >
                  <Icon size={16} strokeWidth={2} aria-hidden />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Identity footer — mirrors the desktop UserMenu header. */}
          {user ? (
            <div className="mt-auto border-t border-[var(--color-border)] pt-4">
              <div className="flex items-center gap-3">
                <span
                  aria-hidden
                  className="grid size-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] text-[11px] font-semibold uppercase text-white"
                >
                  {user.user_id.slice(0, 2)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{user.user_id}</p>
                  <p className="truncate text-[11px] text-[var(--color-muted-foreground)]">
                    {user.department || "—"} · {user.tenant_id}
                  </p>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {user.roles.slice(0, 3).map((role) => (
                  <Badge key={role} variant="muted">
                    {role}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
