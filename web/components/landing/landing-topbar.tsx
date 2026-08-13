"use client";

// LandingTopbar — sticky top navigation for the landing page. Left: the
// wordmark logo. Center: anchor links that scroll-spy the four numbered
// sections (active link gets a lit underline). Right: an auth-adaptive CTA —
// "Open dashboard →" when a session exists, "Sign in →" otherwise.
//
// Auth state is resolved once by the shell and passed in as `authed`; the CTA
// only chooses a target from it and never redirects, because the landing page
// is now a real destination for signed-in users too (CLAUDE.md §25).

import * as React from "react";
import Link from "next/link";
import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface NavItem {
  id: string;
  label: string;
}

export interface LandingTopbarProps {
  items: NavItem[];
  activeId: string;
  onNavigate: (id: string) => void;
  authed: boolean;
}

export function LandingTopbar({ items, activeId, onNavigate, authed }: LandingTopbarProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)]/70 bg-[var(--color-background)]/80 backdrop-blur-lg">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-6">
        <Link
          href="/"
          className="shrink-0 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
        >
          <Logo size={24} />
        </Link>

        <nav aria-label="Sections" className="hidden items-center gap-1 md:flex">
          {items.map((item) => {
            const isActive = item.id === activeId;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                aria-current={isActive ? "true" : undefined}
                className={cn(
                  "relative rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
                  isActive
                    ? "text-[var(--color-foreground)]"
                    : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]",
                )}
              >
                {item.label}
                {isActive ? (
                  <span
                    aria-hidden
                    className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-[var(--color-primary)]"
                  />
                ) : null}
              </button>
            );
          })}
        </nav>

        <Button asChild variant={authed ? "gradient" : "outline"} size="sm">
          <Link href={authed ? "/chat" : "/login"}>
            {authed ? "Open the assistant →" : "Sign in →"}
          </Link>
        </Button>
      </div>
    </header>
  );
}
