"use client";

// SourcesPanel — the right rail that lists evidence chunks next to
// the chat answer. Two consumers:
//   - /chat: passes the live `evidence` array from useStreamingChat
//   - /dashboard: passes nothing; renders the mock `sourceCards` list
//     until a real chat session starts
//
// Per the data-viz skill: rank is the mark identity, the document
// title carries the readable label, the chip + relevance pill give
// quick classification. No series color leaks into text.

import { sourceCards } from "@/lib/mock-data";
import type { RankedEvidence } from "@/lib/types";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { FileText, Quote } from "lucide-react";
import { cn } from "@/lib/utils";

interface SourcesPanelBaseProps {
  /** Eyebrow + header label. Defaults to "Sources". */
  title?: string;
  /** When true, labels all cards as mock and disables interactivity. */
  mock?: boolean;
}

// Discriminated union: passing `evidence` forces live mode; passing
// `mock: true` (or omitting evidence) forces mock mode. The
// `mock?: false` narrow keeps live-mode callers from accidentally
// drifting into the mock branch.
type SourcesPanelProps =
  | { evidence: RankedEvidence[]; mock?: false; title?: string }
  | { evidence?: undefined; mock?: true; title?: string };

export function SourcesPanel(props: SourcesPanelProps) {
  const title = props.title ?? "Sources";
  const isMock = props.mock === true || props.evidence === undefined;

  // Mock mode — render the demo list with file-type chip + relevance pill.
  if (isMock) {
    return (
      <GlassCard>
        <GlassCardHeader className="flex-row items-center justify-between space-y-0">
          <GlassCardTitle>{title}</GlassCardTitle>
          <Badge variant="muted">(Demo data)</Badge>
        </GlassCardHeader>
        <GlassCardContent className="space-y-3">
          {sourceCards.map((s) => (
            <article
              key={s.documentId}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/40 p-3 transition-colors hover:border-[var(--color-primary)]"
            >
              <header className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-2">
                  <FileTypeChip type={s.fileType} />
                  <span className="text-xs font-medium">{s.documentTitle}</span>
                </span>
                <Badge variant="muted">
                  {Math.round(s.relevance * 100)}%
                </Badge>
              </header>
              <p className="mt-2 line-clamp-3 text-[11px] text-[var(--color-muted-foreground)]">
                {s.excerpt}
              </p>
              <footer className="mt-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                <span>{s.sectionTitle}</span>
                <span>{s.documentId}</span>
              </footer>
            </article>
          ))}
        </GlassCardContent>
      </GlassCard>
    );
  }

  // Live mode — render the streamed evidence list.
  const evidence = props.evidence;
  if (evidence.length === 0) {
    return (
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>{title}</GlassCardTitle>
        </GlassCardHeader>
        <GlassCardContent>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Evidence will appear here as soon as the retrieval step
            completes.
          </p>
        </GlassCardContent>
      </GlassCard>
    );
  }

  return (
    <GlassCard>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <GlassCardTitle>{title}</GlassCardTitle>
        <span className="text-[11px] font-medium text-[var(--color-muted-foreground)]">
          {evidence.length} {evidence.length === 1 ? "chunk" : "chunks"}
        </span>
      </GlassCardHeader>
      <GlassCardContent className="space-y-3">
        {evidence.map((s) => (
          <article
            key={s.chunk_id}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/40 p-3"
          >
            <header className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-2">
                <span className="inline-flex size-5 items-center justify-center rounded bg-[var(--color-primary)]/15 font-mono text-[11px] font-semibold text-[var(--color-primary)]">
                  {s.rank}
                </span>
                <span className="text-xs font-medium">{s.document_title}</span>
              </span>
            </header>
            <p className="mt-2 flex gap-2 text-[11px] text-[var(--color-muted-foreground)]">
              <Quote size={11} className="mt-0.5 shrink-0" aria-hidden />
              <span className="line-clamp-3">{s.excerpt}</span>
            </p>
            <footer className="mt-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
              <span>{s.section_title ?? "—"}</span>
              <span className="font-mono">{s.chunk_id}</span>
            </footer>
          </article>
        ))}
      </GlassCardContent>
    </GlassCard>
  );
}

// File-type chip — small monospace pill (MD / PDF / DOCX / TXT).
function FileTypeChip({ type }: { type: "MD" | "PDF" | "DOCX" | "TXT" }) {
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded border px-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider",
        "border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-muted-foreground)]",
      )}
    >
      <FileText size={10} className="mr-1" aria-hidden />
      {type}
    </span>
  );
}
