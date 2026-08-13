"use client";

// LandingFooter — honest closing disclosure. This is a portfolio project over
// synthetic data (CLAUDE.md §3, §22); the footer says so plainly rather than
// implying a production SaaS. The stack row names the real components.

import * as React from "react";
import { Logo } from "@/components/ui/logo";

const STACK = [
  "FastAPI",
  "Next.js 15",
  "ChromaDB",
  "PostgreSQL",
  "BM25 + Dense → RRF → Rerank",
  "Groq / Ollama",
];

export function LandingFooter() {
  return (
    <footer className="border-t border-[var(--color-border)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <Logo size={22} />
          <p className="max-w-md text-[13px] leading-relaxed text-[var(--color-muted-foreground)]">
            A security-aware, evaluation-driven enterprise RAG portfolio
            project. All company documents and records are synthetic — no real
            confidential data.
          </p>
        </div>
        <ul className="flex flex-wrap gap-2 sm:max-w-xs sm:justify-end">
          {STACK.map((item) => (
            <li
              key={item}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-muted)]/30 px-2 py-1 font-mono text-[11px] text-[var(--color-muted-foreground)]"
            >
              {item}
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
