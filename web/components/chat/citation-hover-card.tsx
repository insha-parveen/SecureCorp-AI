// Citation hover card — Radix Popover. Click to toggle on touch devices,
// hover on the desktop. The card shows the excerpt + document + section
// title. Dismissed on outside click.

"use client";

import * as Popover from "@radix-ui/react-popover";
import type { RankedEvidence } from "@/lib/types";

export function CitationHoverCard({
  evidence,
  children,
}: {
  evidence: RankedEvidence;
  children: React.ReactNode;
}) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>{children}</Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={6}
          className="z-20 w-80 rounded-md border border-[var(--color-border)] bg-[var(--color-card)] p-3 text-sm text-[var(--color-card-foreground)] shadow-md"
          aria-describedby="citation-excerpt"
        >
          <div className="mb-1 flex items-center justify-between text-xs text-[var(--color-muted-foreground)]">
            <span className="font-mono">{evidence.document_id}</span>
            <span>#{evidence.rank}</span>
          </div>
          <p id="citation-excerpt" className="text-xs leading-relaxed">
            {evidence.excerpt}
          </p>
          {evidence.section_title ? (
            <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
              {evidence.section_title}
            </p>
          ) : null}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
