"use client";

// /knowledge — corpus overview. Mock-only at MVP; once a real
// ingestion-status endpoint exists, swap the fetcher without touching
// the panel layout.
//
// Layout: a search input + a virtualized-feeling file grid (just a
// regular grid for now; the corpus is small enough to render all
// 275 documents). Each card shows the document id, type chip,
// department, classification, and the chunk count.

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, FileText, FolderOpen } from "lucide-react";

interface MockDoc {
  id: string;
  title: string;
  department: string;
  type: "policy" | "knowledge_base" | "email" | "meeting" | "slack" | "jira" | "github";
  classification: "public" | "internal" | "confidential" | "restricted";
  chunks: number;
}

// A representative slice of the corpus. The real corpus has 275
// documents; rendering 30 cards on the page is the right density.
const MOCK_DOCS: MockDoc[] = [
  { id: "HR-002", title: "Leave Policy", department: "HR", type: "policy", classification: "internal", chunks: 8 },
  { id: "HR-007", title: "Remote Work Policy", department: "HR", type: "policy", classification: "internal", chunks: 6 },
  { id: "IT-001", title: "Information Security Policy", department: "IT", type: "policy", classification: "confidential", chunks: 12 },
  { id: "IT-005", title: "Password and Authentication Policy", department: "IT", type: "policy", classification: "confidential", chunks: 4 },
  { id: "FIN-001", title: "Procurement Policy", department: "Finance", type: "policy", classification: "internal", chunks: 7 },
  { id: "FIN-002", title: "Invoice Approval SOP", department: "Finance", type: "knowledge_base", classification: "internal", chunks: 5 },
  { id: "OPS-001", title: "Project Management SOP", department: "Operations", type: "knowledge_base", classification: "internal", chunks: 9 },
  { id: "OPS-002", title: "Vendor Onboarding SOP", department: "Operations", type: "knowledge_base", classification: "internal", chunks: 5 },
  { id: "SEC-001", title: "Security Incident Response SOP", department: "IT", type: "knowledge_base", classification: "restricted", chunks: 10 },
  { id: "HR-013", title: "Q3 All-Hands Email Thread", department: "HR", type: "email", classification: "internal", chunks: 1 },
  { id: "IT-021", title: "Slack #security-incident 2026-01-12", department: "IT", type: "slack", classification: "restricted", chunks: 1 },
  { id: "ENG-031", title: "GitHub PR #1287 — ingest retry", department: "Engineering", type: "github", classification: "internal", chunks: 1 },
  { id: "OPS-014", title: "Operations weekly 2026-02-03", department: "Operations", type: "meeting", classification: "internal", chunks: 4 },
  { id: "FIN-019", title: "Q4 expense review", department: "Finance", type: "jira", classification: "internal", chunks: 1 },
];

const CLASSIFICATION_VARIANT: Record<
  MockDoc["classification"],
  "success" | "warning" | "critical" | "accent"
> = {
  public: "success",
  internal: "accent",
  confidential: "warning",
  restricted: "critical",
};

export default function KnowledgePage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return MOCK_DOCS;
    return MOCK_DOCS.filter(
      (d) =>
        d.id.toLowerCase().includes(q) ||
        d.title.toLowerCase().includes(q) ||
        d.department.toLowerCase().includes(q),
    );
  }, [query]);

  return (
    <>
      <PageHeader title="Knowledge" eyebrow="Corpus" />
      <div className="space-y-6 p-4 sm:p-6">
        <header className="flex items-center justify-between gap-3">
          <div className="relative max-w-md flex-1">
            <Search
              size={14}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted-foreground)]"
              aria-hidden
            />
            <Input
              type="search"
              placeholder="Search by ID, title, or department…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
              aria-label="Search corpus"
            />
          </div>
          <div className="flex items-center gap-2 text-[11px] text-[var(--color-muted-foreground)]">
            <FolderOpen size={12} aria-hidden />
            <span>{MOCK_DOCS.length} of 275 documents · indexed</span>
            <Badge variant="muted">(Demo data)</Badge>
          </div>
        </header>

        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Indexed documents</GlassCardTitle>
          </GlassCardHeader>
          <GlassCardContent>
            <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filtered.map((d) => (
                <li
                  key={d.id}
                  className="group rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/40 p-3 transition-colors hover:border-[var(--color-primary)]"
                >
                  <header className="flex items-start justify-between gap-2">
                    <span className="inline-flex items-center gap-2">
                      <FileText
                        size={14}
                        aria-hidden
                        className="text-[var(--color-muted-foreground)] group-hover:text-[var(--color-primary)]"
                      />
                      <span className="font-mono text-[11px] text-[var(--color-muted-foreground)]">
                        {d.id}
                      </span>
                    </span>
                    <Badge variant={CLASSIFICATION_VARIANT[d.classification]}>
                      {d.classification}
                    </Badge>
                  </header>
                  <p className="mt-2 line-clamp-2 text-sm font-medium">{d.title}</p>
                  <footer className="mt-3 flex items-center justify-between text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                    <span>{d.department}</span>
                    <span>{d.chunks} chunks</span>
                  </footer>
                </li>
              ))}
              {filtered.length === 0 ? (
                <li className="col-span-full rounded-md border border-dashed border-[var(--color-border)] p-6 text-center text-xs text-[var(--color-muted-foreground)]">
                  No documents match &ldquo;{query}&rdquo;.
                </li>
              ) : null}
            </ul>
          </GlassCardContent>
        </GlassCard>
      </div>
    </>
  );
}