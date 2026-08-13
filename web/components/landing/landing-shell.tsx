"use client";

// LandingShell — the client half of the landing page. Owns the two pieces of
// shared state the sections need: the current section (scroll-spy) and the
// auth flag (resolved once, used only to point the CTAs at /dashboard vs
// /login — never to redirect). Everything below composes stateless section
// components from components/landing/*.
//
// The architecture section embeds the REAL <SecureCorpPipeline/> (via
// LandingPipelineShowcase, which just feeds it props) — §26.6 calls for the
// pipeline as the interactive architecture showcase. Here it replays the real
// DOCUMENT_RAG trace on a loop so it animates; reduced-motion shows the
// completed path statically. No pipeline logic is forked — same reducer.

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { me } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth-context";
import { LandingPipelineShowcase } from "@/components/landing/pipeline-showcase";
import { LandingTopbar, type NavItem } from "@/components/landing/landing-topbar";
import { Hero } from "@/components/landing/hero";
import { StatStrip } from "@/components/landing/stat-strip";
import { Section } from "@/components/landing/section";
import { RetrievalProbe } from "@/components/landing/retrieval-probe";
import { SecurityModel } from "@/components/landing/security-model";
import { EvidenceDemo } from "@/components/landing/evidence-demo";
import { CtaBand } from "@/components/landing/cta-band";
import { LandingFooter } from "@/components/landing/landing-footer";
import { useSectionNav } from "@/hooks/use-section-nav";

// The four numbered sections ARE the real request sequence, so the nav order
// and the 01–04 numbering both encode the order a query flows through.
const NAV_ITEMS: NavItem[] = [
  { id: "architecture", label: "The path" },
  { id: "retrieval", label: "Retrieval" },
  { id: "security", label: "Security" },
  { id: "evidence", label: "Evidence" },
];

export function LandingShell() {
  const { user, setUser } = useCurrentUser();

  // Resolve session once for CTA targeting. Never redirects.
  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: me,
    enabled: user === null,
    retry: false,
    staleTime: 60_000,
  });

  React.useEffect(() => {
    if (!user && meQuery.data) setUser(meQuery.data);
  }, [user, meQuery.data, setUser]);

  const authed = Boolean(user ?? meQuery.data);

  const sectionIds = React.useMemo(() => NAV_ITEMS.map((i) => i.id), []);
  const { active, go } = useSectionNav(sectionIds);

  return (
    <div className="min-h-dvh bg-[var(--color-background)] text-[var(--color-foreground)]">
      <LandingTopbar items={NAV_ITEMS} activeId={active} onNavigate={go} authed={authed} />

      <main>
        <Hero authed={authed} />
        <StatStrip />

        <Section
          id="architecture"
          index="01"
          kicker="The path"
          title="What actually happens to a query"
          lead="Every request runs the same pipeline: authenticate, authorize, then route to hybrid document search, an authorized SQL path, or a safe refusal — before any evidence reaches the model. This is the real component the chat surface animates live."
        >
          <LandingPipelineShowcase title="Request pipeline — authorization before retrieval" />
        </Section>

        <Section
          id="retrieval"
          index="02"
          kicker="Retrieval"
          title="Hybrid search, not just vectors"
          lead="Dense retrieval alone misses exact identifiers — invoice numbers, policy codes, employee IDs. BM25 catches them. The two ranked lists fuse with Reciprocal Rank Fusion, then a cross-encoder reranks the bounded candidate set."
        >
          <RetrievalProbe />
        </Section>

        <Section
          id="security"
          index="03"
          kicker="Security"
          title="Authorization at the boundary"
          lead="Roles and tenants are enforced in application code and the data-access layer — never inferred by the LLM. The client-supplied role is never trusted; the authenticated identity comes from a verified server-side token."
        >
          <SecurityModel />
        </Section>

        <Section
          id="evidence"
          index="04"
          kicker="Evidence"
          title="Answers you can trace back"
          lead="Citations are validated server-side and resolve to real indexed chunks or structured records. Structured questions take the SQL route; document questions take hybrid retrieval. Both return evidence you can open."
        >
          <EvidenceDemo />
        </Section>

        <CtaBand authed={authed} />
      </main>

      <LandingFooter />
    </div>
  );
}
