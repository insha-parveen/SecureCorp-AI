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

// Corpus scale — measured from data/processed/chunks.jsonl (2026-08-18).
export const CORPUS_STATS: Fact[] = [
  { value: "276", label: "documents ingested", source: "measured · chunks.jsonl" },
  { value: "455", label: "retrieval chunks", source: "measured · one BM25 + dense corpus" },
  { value: "125,813", label: "body tokens (exact)", source: "measured · MiniLM tokenizer" },
  { value: "6", label: "application roles", source: "§11 · RBAC" },
];

// Per-source-type doc/chunk counts — measured from chunks.jsonl (2026-08-18).
// Chunk column sums to 455; doc column sums to 276.
export const SOURCE_BREAKDOWN: { type: string; docs: number; chunks: number }[] = [
  { type: "email", docs: 162, chunks: 162 },
  { type: "policy", docs: 19, chunks: 101 },
  { type: "knowledge_base", docs: 11, chunks: 70 },
  { type: "meeting", docs: 12, chunks: 48 },
  { type: "slack", docs: 27, chunks: 28 },
  { type: "jira", docs: 25, chunks: 26 },
  { type: "github", docs: 20, chunks: 20 },
];

// Retrieval configuration — mirrors src/hybridrag/config.py defaults.
export const RETRIEVAL_CONFIG = {
  embeddingModel: "sentence-transformers/all-MiniLM-L6-v2",
  embeddingDims: 384,
  distance: "cosine",
  reranker: "cross-encoder/ms-marco-MiniLM-L6-v2",
  // Retuned 60 -> 10: at k=60 the 1/(k+rank) weights flatten so much that
  // fusion scored BELOW its own inputs. See config.py for the measurement.
  rrfK: 10,
  bm25K1: 1.5,
  bm25B: 0.75,
  vocab: "5,550",
} as const;

// The diagnostic identifier probe — CLAUDE.md §7 "Why it earns its place".
// This is EXPLICITLY a diagnostic that justifies keeping BM25, NOT a Phase 8
// retrieval-quality benchmark. It asks a narrow question: for the 40 identifiers
// that occur in exactly one chunk, does the retriever put THAT chunk first?
// It is NOT the general Hit@1 of either retriever (dense Hit@1 on the golden
// set is far higher) — the labels must never imply otherwise.
export const BM25_PROBE = {
  identifiers: 40,
  bm25HitAt1: 40,
  denseHitAt1: 4,
  caveat:
    "Diagnostic probe over 40 single-chunk identifiers — not the Phase 8 evaluation, " +
    "and not either retriever's general Hit@1.",
  source: "§7 · Retrieval Strategy",
} as const;

// The six canonical application roles — CLAUDE.md §3 / §11.
export const ROLES = ["employee", "manager", "hr", "finance", "it", "admin"] as const;

// Retrieval ablation — REAL measured numbers, authorization enforced (the
// production path), RRF k=10 + identifier-aware reranker bypass. Two splits:
// the 80-query legacy set and the 64-item answerable holdout (final reporting).
// Source: evaluation/reports/legacy_authfixed.json + holdout_authfixed.json.
// These are genuine measurements, so unlike RAGAS/latency they belong on the
// page (the honesty guard forbids only UNmeasured metrics).
export interface AblationRow {
  strategy: string;
  recallAt5: number; // 0..1
  hitAt1: number; // 0..1
  best?: boolean;
}

export const RETRIEVAL_ABLATION_HOLDOUT: AblationRow[] = [
  { strategy: "Dense-only", recallAt5: 0.8438, hitAt1: 0.3906 },
  { strategy: "BM25-only", recallAt5: 0.8594, hitAt1: 0.5938 },
  { strategy: "Hybrid (RRF)", recallAt5: 0.9062, hitAt1: 0.4688, best: true },
  { strategy: "Hybrid + Rerank", recallAt5: 0.875, hitAt1: 0.5312 },
];

// Headline retrieval result for the hero/stat strip. The 80q legacy set reaches
// 95.00% Hybrid-RRF Recall@5 against a measured 96.25% achievable ceiling.
export const RETRIEVAL_HEADLINE = {
  bestRecallAt5: "95.0%",
  bestArm: "Hybrid (RRF)",
  ceiling: "96.25%",
  split: "80-query dev set · authorization enforced",
  source: "evaluation/reports/legacy_authfixed.json",
} as const;

// The two tenants used to prove isolation — CLAUDE.md §6 / seed_db.py.
export const TENANTS = ["nexacore_main", "nexacore_global"] as const;

// Retrieval pipeline stages, in order — CLAUDE.md §7. Rendered as the
// retrieval section's ordered flow (BM25 + Dense → RRF → Rerank → Top-K).
export const RETRIEVAL_STAGES: { name: string; detail: string }[] = [
  { name: "BM25", detail: "Exact identifiers, policy codes, acronyms" },
  { name: "Dense", detail: "Semantic similarity over 384-dim vectors" },
  { name: "RRF", detail: "Reciprocal Rank Fusion by unique chunk_id, k=10" },
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
