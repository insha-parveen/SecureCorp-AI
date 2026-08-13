"use client";

// CtaBand — the closing invitation. When signed out, the real demo accounts
// are surfaced right here (one click → the assistant) via DemoUserStrip,
// instead of bouncing to /login. When signed in, a single CTA opens the
// assistant. The demo-user path remains the underlying auth (CLAUDE.md §24.5).

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { DemoUserStrip } from "@/components/landing/demo-user-strip";

export interface CtaBandProps {
  authed: boolean;
}

export function CtaBand({ authed }: CtaBandProps) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)]/50 px-8 py-14 text-center backdrop-blur-md">
        {/* Faint top-edge violet hairline, matching the login card. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent, color-mix(in oklch, var(--color-accent-violet) 70%, transparent), transparent)",
          }}
        />
        <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
          Sign in and ask it something.
        </h2>
        <p className="mx-auto mt-4 max-w-lg text-[15px] leading-relaxed text-[var(--color-muted-foreground)]">
          Six pre-seeded demo accounts, one per role. Watch the request pipeline
          animate live as your question is authorized, routed, retrieved, and
          cited.
        </p>

        {authed ? (
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button asChild variant="gradient" size="lg">
              <Link href="/chat">Open the assistant</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="#architecture">Review the architecture</a>
            </Button>
          </div>
        ) : (
          <>
            {/* One-click demo accounts — the prominent, visible sign-in path. */}
            <DemoUserStrip className="mt-8" />
            <div className="mt-6 flex items-center justify-center">
              <Button asChild variant="outline" size="sm">
                <Link href="/login">Use the full sign-in form →</Link>
              </Button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
