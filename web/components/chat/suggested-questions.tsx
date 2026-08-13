// Suggested questions rendered on the empty state. MVP: hard-coded list
// — `/api/suggested-questions` is a stretch goal. The six prompts cover
// the canonical categories from CLAUDE.md §14 so a tester can exercise
// most of the pipeline in one click.

"use client";

const SUGGESTIONS: Array<{ title: string; prompt: string }> = [
  {
    title: "Remote work",
    prompt: "What is the remote work policy?",
  },
  {
    title: "Leave entitlement",
    prompt: "How many days of leave do employees get per year?",
  },
  {
    title: "Invoice lookup",
    prompt: "What is the total of invoice INV-2026-0108?",
  },
  {
    title: "Open tickets",
    prompt: "How many open IT tickets are there?",
  },
  {
    title: "Password policy",
    prompt: "What is the password rotation policy?",
  },
  {
    title: "Expense claim",
    prompt: "Show me my own expense claims.",
  },
];

export function SuggestedQuestions({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
      {SUGGESTIONS.map((s, i) => (
        <button
          key={s.title}
          type="button"
          onClick={() => onSelect(s.prompt)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)] p-3 text-left text-sm transition-colors hover:border-[var(--color-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <span className="block font-medium">{s.title}</span>
          <span className="block text-xs text-[var(--color-muted-foreground)]">
            {s.prompt}
          </span>
        </button>
      ))}
    </div>
  );
}
