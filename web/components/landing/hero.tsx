"use client";

// Hero — the page's thesis (frontend-design: "the hero is a thesis"). The
// single most characteristic claim in this system's world is that
// authorization runs BEFORE retrieval and unauthorized chunks reaching the
// LLM = 0. That claim is the headline, set in the display face, paired with
// a real example request trace (the signature motif) so the promise is shown
// as machine output, not marketing copy.
//
// The ambient backdrop is CONTAINED to the hero (absolute, not fixed): a
// login-style radial glow anchored to this section only. We deliberately do
// not reuse <LoginBackdrop/> here — its `fixed inset-0` is built for a
// single-screen login and would escape onto the whole long-scroll page.

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TraceCard } from "@/components/landing/trace-card";
import { EXAMPLE_TRACE } from "@/lib/landing-facts";

export interface HeroProps {
  /** True when a session already exists; flips the primary CTA target. */
  authed: boolean;
}

export function Hero({ authed }: HeroProps) {
  return (
    <section className="relative isolate overflow-hidden">
      {/* Contained ambient glow — matches the login atmosphere without the
          fixed-position full-bleed backdrop. Static; nothing to reduce. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 30% 20%, color-mix(in oklch, var(--color-primary) 12%, transparent) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 85% 15%, color-mix(in oklch, var(--color-accent-violet) 10%, transparent) 0%, transparent 55%)",
        }}
      />
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-20 sm:py-28 lg:grid-cols-[1.1fr_0.9fr]">
        {/* Left: the claim. */}
        <div className="relative z-10">
          <Badge variant="accent" className="mb-6 font-mono">
            HybridRAG · BM25 + Dense · Reranked
          </Badge>
          <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
            Authorization happens{" "}
            <span className="bg-gradient-to-r from-[var(--color-accent-violet)] via-[var(--color-primary)] to-[var(--color-series-2)] bg-clip-text text-transparent">
              before
            </span>{" "}
            retrieval.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-[var(--color-muted-foreground)] sm:text-lg">
            SecureCorp AI answers questions over enterprise documents and
            structured records — with hybrid search, cross-encoder reranking,
            and server-validated citations. Evidence is filtered by who&rsquo;s
            asking, never after the fact. Unauthorized chunks reaching the model:{" "}
            <span className="font-mono font-medium text-[var(--color-success)]">0</span>.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild variant="gradient" size="lg">
              <Link href={authed ? "/chat" : "/login"}>
                {authed ? "Open the assistant" : "Sign in and ask it something"}
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="#architecture">See the request path</a>
            </Button>
          </div>
        </div>

        {/* Right: a real observed request, shown as trace output. */}
        <div className="relative z-10">
          <TraceCard
            label="example request"
            prompt={EXAMPLE_TRACE.query}
            lines={[
              { key: "user", value: `${EXAMPLE_TRACE.user} (${EXAMPLE_TRACE.roles})`, tone: "value" },
              { key: "tenant", value: EXAMPLE_TRACE.tenant, tone: "muted" },
              { key: "authz", value: EXAMPLE_TRACE.authz, tone: "pass", ok: true },
              { key: "route", value: EXAMPLE_TRACE.route, tone: "route-rag" },
              { key: "cache", value: EXAMPLE_TRACE.cacheTier, tone: "muted" },
              { key: "evidence", value: `${EXAMPLE_TRACE.evidenceCount} chunks`, tone: "value" },
              { key: "cites", value: `[${EXAMPLE_TRACE.citations.join(", ")}]`, tone: "pass", ok: true },
            ]}
            footer={EXAMPLE_TRACE.source}
          />
        </div>
      </div>
    </section>
  );
}
