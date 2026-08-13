// Citation chip — a button that looks like a superscript. Wraps a
// HoverCard so each [N] in the assistant's answer is keyboard-accessible
// and announces the source on focus.

"use client";

import { CitationHoverCard } from "./citation-hover-card";
import type { RankedEvidence } from "@/lib/types";

export function CitationChip({
  rank,
  evidence,
}: {
  rank: number;
  evidence: RankedEvidence[] | undefined;
}) {
  const item = evidence?.find((e) => e.rank === rank);
  if (!item) {
    return (
      <span
        aria-label={`Citation ${rank} (unavailable)`}
        className="text-[var(--color-muted-foreground)]"
      >
        [{rank}]
      </span>
    );
  }
  return (
    <CitationHoverCard evidence={item}>
      <button
        type="button"
        className="mx-0.5 align-baseline text-xs font-semibold text-[var(--color-primary)] hover:underline"
        aria-describedby="citation-excerpt"
        aria-label={`Citation ${rank} from ${item.document_id}`}
      >
        [{rank}]
      </button>
    </CitationHoverCard>
  );
}
