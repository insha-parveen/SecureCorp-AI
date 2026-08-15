// Landing-page facts — the single source of every number the marketing page
// renders. CLAUDE.md §20 and §24.5 forbid inventing benchmark values: each
// entry below is a REAL measurement with its source noted, or it does not
// belong here. Values that have no real measurement yet (RAGAS scores,
// latency, cache-hit rate) are deliberately ABSENT — do not add them until a
// Phase 8 run produces them.
//
// Sources are CLAUDE.md sections; the example trace is a real observed run
// from the 2026-08-12 end-to-end drive (all four scenarios green).

export interface Fact {
  /** The measured value, preformatted for display. */
  value: string;
  /** What it measures, in end-user language. */
  label: string;
  /** Where the number comes from (shown as a small citation). */
  source: string;
}

// Corpus scale — CLAUDE.md §9b "Document Corpus — AS BUILT".
export const CORPUS_STATS: Fact[] = [
  { value: "275", label: "documents ingested", source: "§9b · from 260 Markdown files" },
  { value: "450", label: "retrieval chunks", source: "§9b · one BM25 + dense corpus" },
  { value: "124,472", label: "body tokens (exact)", source: "§9b · MiniLM tokenizer" },
  { value: "6", label: "application roles", source: "§11 · RBAC" },
];

// Per-source-type chunk counts — CLAUDE.md §9b table. Used by the corpus
// breakdown; the sum is 450 by construction.
export const SOURCE_BREAKDOWN: { type: string; docs: number; chunks: number }[] = [
  { type: "email", docs: 165, chunks: 162 },
  { type: "policy", docs: 19, chunks: 101 },
  { type: "knowledge_base", docs: 10, chunks: 65 },
  { type: "meeting", docs: 13, chunks: 48 },
  { type: "slack", docs: 27, chunks: 28 },
  { type: "jira", docs: 21, chunks: 26 },
  { type: "github", docs: 20, chunks: 20 },
];

// Retrieval configuration — CLAUDE.md §7 "Retrieval Strategy" / "AS BUILT".
export const RETRIEVAL_CONFIG = {
  embeddingModel: "sentence-transformers/all-MiniLM-L6-v2",
  embeddingDims: 384,
  distance: "cosine",
  reranker: "cross-encoder/ms-marco-MiniLM-L6-v2",
  rrfK: 60,
  bm25K1: 1.5,
  bm25B: 0.75,
  vocab: "5,550",
} as const;

// The diagnostic identifier probe — CLAUDE.md §7 "Why it earns its place".
// This is EXPLICITLY a diagnostic that justifies keeping BM25, NOT a Phase 8
// retrieval-quality benchmark. The label must always say so.
export const BM25_PROBE = {
  identifiers: 40,
  bm25HitAt1: 40,
  denseHitAt1: 4,
  caveat: "Diagnostic probe over 40 single-chunk identifiers — not the Phase 8 evaluation.",
  source: "§7 · Retrieval Strategy",
} as const;

// The six canonical application roles — CLAUDE.md §3 / §11.
export const ROLES = ["employee", "manager", "hr", "finance", "it", "admin"] as const;

// The two tenants used to prove isolation — CLAUDE.md §6 / seed_db.py.
export const TENANTS = ["nexacore_main", "nexacore_global"] as const;

// Retrieval pipeline stages, in order — CLAUDE.md §7. Rendered as the
// retrieval section's ordered flow (BM25 + Dense → RRF → Rerank → Top-K).
export const RETRIEVAL_STAGES: { name: string; detail: string }[] = [
  { name: "BM25", detail: "Exact identifiers, policy codes, acronyms" },
  { name: "Dense", detail: "Semantic similarity over 384-dim vectors" },
  { name: "RRF", detail: "Reciprocal Rank Fusion by unique chunk_id, k=60" },
  { name: "Rerank", detail: "Cross-encoder on the bounded candidate set" },
];

// A REAL observed request from the 2026-08-12 end-to-end drive, used by the
// hero trace card and the evidence section. These are the actual events the
// pipeline emitted for this query (route, cache tier, evidence count,
// server-validated citations) — presented as an "example request", never as
// an aggregate metric.
export const EXAMPLE_TRACE = {
  query: "What is the remote work policy?",
  user: "alice",
  roles: "hr, employee",
  tenant: "nexacore_main",
  route: "DOCUMENT_RAG",
  cacheTier: "MISS",
  authz: "PASS",
  evidenceCount: 5,
  citations: [3, 1, 2, 5],
  topChunkId: "HR-003:v1:0000",
  model: "llama-3.3-70b-versatile",
  source: "Observed e2e run · 2026-08-12",
} as const;

// A second real trace: the structured-SQL path (invoice lookup). Shown in the
// evidence/architecture context to demonstrate the non-RAG branch. Also from
// the 2026-08-12 drive.
export const EXAMPLE_SQL_TRACE = {
  query: "What is the total of invoice INV-2026-0108?",
  user: "bob",
  roles: "finance, employee",
  route: "STRUCTURED_SQL",
  cacheTier: "MISS",
  authz: "PASS",
  answer: "The total of invoice INV-2026-0108 is $8,869.26.",
  source: "Observed e2e run · 2026-08-12",
} as const;
