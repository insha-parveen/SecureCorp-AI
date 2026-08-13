"use client";

// LoginCard — the centered glass treatment that wraps the sign-in form.
// Sits on top of <LoginBackdrop/> and inside <Providers/>. By design it
// is only used on /login — other authenticated surfaces use SidebarNav.
//
// Per §24.5 the email + password fields are cosmetic; the form still
// POSTs to /api/auth/token with `{ user_id }` derived from the email
// prefix by LoginForm. The SSO alternative is also visual-only for
// MVP and just routes through the same picker if the user wires it.

import * as React from "react";
import { LoginForm } from "@/components/auth/login-form";
import { Logo } from "@/components/ui/logo";
import { Badge } from "@/components/ui/badge";

export function LoginCard() {
  return (
    <div className="relative z-10 w-full max-w-md">
      {/* Wordmark + project kicker above the glass card. */}
      <div className="mb-6 flex flex-col items-center gap-3 text-center">
        <Logo size={36} withWordmark={false} />
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">SecureCorp AI</h1>
          <p className="text-sm text-[var(--color-muted-foreground)]">
            Enterprise knowledge, answered with citations.
          </p>
        </div>
      </div>

      {/* The glass card itself. LoginForm owns its internals. */}
      <div
        className="relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)]/65 p-6 shadow-[inset_0_1px_0_0_rgb(255_255_255_/_0.04),0_24px_60px_-30px_rgb(0_0_0_/_0.6)] backdrop-blur-xl"
      >
        {/* Subtle inner gradient — violet hint at the top edge. Stays well under
            the foreground contrast threshold; no text sits on it. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent, color-mix(in oklch, var(--color-accent-violet) 70%, transparent), transparent)",
          }}
        />
        <LoginForm />

        {/* Footer: trust badge (per the reference image). Static string. */}
        <div className="mt-5 flex items-center justify-center gap-2 text-[11px] uppercase tracking-wide text-[var(--color-muted-foreground)]">
          <Badge variant="accent">SOC 2</Badge>
          <span>Protected by enterprise-grade security</span>
        </div>
      </div>
    </div>
  );
}
