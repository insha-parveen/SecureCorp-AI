// Renders an assistant message. Splits the visible text on citation
// tokens of the form [N]; each match becomes a <CitationChip>. The
// trailing caret is shown via the .streaming-caret CSS animation,
// which respects prefers-reduced-motion.
//
// Streaming-display contract:
//
//   - While evidence is arriving (no tokens yet, no done): show a
//     "thinking…" placeholder so the user knows the retrieval step is
//     still in flight.
//   - While tokens are arriving (text length > 0, no done yet): hide
//     the streaming tokens. The wire-format drops `format: json_object`
//     on the streaming path but the model still emits the JSON
//     envelope token-by-token (Groq's prompt follows through on the
//     JSON contract), so revealing raw tokens would flash
//     `{"answer": "...` at the user.
//   - When the `done` event fires, reveal the parsed `done.answer`
//     prose. This is the actual answer.

"use client";

import { Fragment } from "react";
import { Loader2 } from "lucide-react";
import { CitationChip } from "./citation-chip";
import type { AssistantMessage } from "@/lib/types";

const CITATION_RE = /\[(\d+)\]/g;

function renderAnswer(text: string, evidence: AssistantMessage["evidence"]) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = CITATION_RE.exec(text)) !== null) {
    const idx = match.index;
    if (idx > lastIndex) {
      parts.push(<Fragment key={key++}>{text.slice(lastIndex, idx)}</Fragment>);
    }
    const rank = Number(match[1]);
    parts.push(<CitationChip key={key++} rank={rank} evidence={evidence} />);
    lastIndex = idx + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(<Fragment key={key++}>{text.slice(lastIndex)}</Fragment>);
  }
  return parts;
}

export function StreamingAnswer({ message }: { message: AssistantMessage }) {
  if (message.error) {
    return (
      <div
        role="alert"
        className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-3 text-sm text-[var(--color-destructive)]"
      >
        {message.error.message}
      </div>
    );
  }

  // No tokens yet AND no done — retrieval / routing still in flight.
  // The parent already has the sources panel; show a quiet placeholder.
  if (!message.text && !message.done) {
    return (
      <p
        className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted-foreground)]"
        aria-live="polite"
      >
        <Loader2 size={12} className="animate-spin" aria-hidden />
        <span>Thinking…</span>
      </p>
    );
  }

  // A real response carries either evidence (rag path) or citations;
  // a cache hit or an explicit REFUSE comes back with both empty. In
  // those cases the prose IS the answer — render it as muted italic so
  // the [N] chips don't appear with no backing sources.
  const isAbstention =
    message.done !== null &&
    message.done.citations.length === 0 &&
    message.done.evidence.length === 0;

  if (isAbstention) {
    return (
      <p className="text-sm italic text-[var(--color-muted-foreground)]">
        {message.done?.answer || message.text || "I'm not sure how to answer that."}
      </p>
    );
  }

  // While streaming, hide the raw JSON envelope tokens and show the
  // caret spinner instead. On `done`, reveal the parsed answer prose.
  const visibleText = message.done?.answer ?? (message.done ? "" : null);
  if (visibleText === null) {
    // Tokens are still flowing — show a thinking indicator.
    return (
      <p
        className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted-foreground)]"
        aria-live="polite"
      >
        <Loader2 size={12} className="animate-spin" aria-hidden />
        <span>Thinking…</span>
      </p>
    );
  }

  if (!visibleText) {
    // Done arrived but no parseable answer — fall back to raw text.
    return (
      <p className="text-sm leading-relaxed">{message.text || "—"}</p>
    );
  }

  return (
    <p
      aria-live="polite"
      className="text-sm leading-relaxed"
    >
      {renderAnswer(visibleText, message.evidence)}
    </p>
  );
}