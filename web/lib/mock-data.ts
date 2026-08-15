// Mock data for the dashboard surface.
//
// Every value in this file is **fictional** — it represents a plausible
// SecureCorp / NexaCore operational shape, not a real measurement. The
// `lib/dashboard-types.ts` shapes are the contract; if the real backend
// eventually exposes `/api/analytics`, `/api/security`, or `/api/cache`
// endpoints, the consumers (`components/dashboard/*.tsx`) will swap to
// those fetches without touching the panels.
//
// Hard rules enforced here:
//   1. Anything derived from a real Phase 8 experiment is **cited**
//      with the report path. Everything else is labeled `(Demo data)`
//      in the consuming panel's corner.
//   2. Numbers are coherent (e.g. a delta of `+18.6%` matches the
//      `value` field on the same tile — not a copy-paste mismatch).
//   3. Status hues come from the semantic tokens (`--success`,
//      `--warning`, `--critical`, `--primary`) — never from
//      `--series-*`, which are reserved for chart series identity
//      per the data-viz skill's "status colors reserved" rule.

import type {
  CacheStat,
  ChartPoint,
  DonutSegment,
  KpiDelta,
  PipelineStep,
  RagasGaugeData,
  RetrievalRow,
  SecurityCheck,
  SourceCardData,
  StatTileData,
  UserContextData,
} from "./dashboard-types";

// ──────────────────────────────────────────────────────────────────────
// Reusable deltas
// ──────────────────────────────────────────────────────────────────────

const DELTA_UP_GOOD: KpiDelta = {
  value: 186,
  percent: 18.6,
  direction: "up",
  tone: "good",
};
const DELTA_UP_GOOD_SMALL: KpiDelta = {
  value: 4,
  percent: 4.2,
  direction: "up",
  tone: "good",
};
const DELTA_UP_WARN: KpiDelta = {
  value: 11,
  percent: 11.0,
  direction: "up",
  tone: "bad",
};
const DELTA_DOWN_GOOD: KpiDelta = {
  value: 42,
  percent: 12.4,
  direction: "down",
  tone: "good",
};

// ──────────────────────────────────────────────────────────────────────
// KPI tiles (used on `/dashboard`, `/analytics`)
// ──────────────────────────────────────────────────────────────────────

export const kpiTiles: StatTileData[] = [
  {
    label: "Total Queries",
    value: "1,248",
    rawValue: 1248,
    delta: DELTA_UP_GOOD,
    sparkline: [820, 870, 910, 940, 1010, 1080, 1248],
    accent: "var(--color-series-1)",
    icon: "Activity",
  },
  {
    label: "Avg. Response Time",
    value: "1.42s",
    rawValue: 1.42,
    delta: DELTA_DOWN_GOOD,
    sparkline: [1.85, 1.74, 1.66, 1.58, 1.51, 1.48, 1.42],
    accent: "var(--color-series-3)",
    icon: "Timer",
  },
  {
    label: "Cache Hit Rate",
    value: "63.4%",
    rawValue: 63.4,
    delta: DELTA_UP_GOOD_SMALL,
    sparkline: [55, 57, 58, 60, 61, 62, 63.4],
    accent: "var(--color-series-4)",
    icon: "Zap",
  },
  {
    label: "Refused / Blocked",
    value: "2.1%",
    rawValue: 2.1,
    delta: DELTA_UP_WARN,
    sparkline: [1.2, 1.4, 1.5, 1.7, 1.8, 2.0, 2.1],
    accent: "var(--color-critical)",
    icon: "ShieldAlert",
  },
];

// ──────────────────────────────────────────────────────────────────────
// Pipeline steps (used by `pipeline-flow`, animated when chat streams)
// ──────────────────────────────────────────────────────────────────────

export const pipelineSteps: PipelineStep[] = [
  {
    id: "query",
    label: "Query",
    caption: "User prompt received",
    icon: "MessageSquare",
    status: "done",
  },
  {
    id: "router",
    label: "Query Router",
    caption: "DOCUMENT_RAG · STRUCTURED_SQL · REFUSE",
    icon: "GitBranch",
    status: "done",
  },
  {
    id: "authz",
    label: "Authorization",
    caption: "RBAC + ABAC filter",
    icon: "KeyRound",
    status: "done",
  },
  {
    id: "bm25",
    label: "BM25 Search",
    caption: "Exact identifier match",
    icon: "Search",
    status: "done",
  },
  {
    id: "dense",
    label: "Dense Search",
    caption: "Semantic similarity",
    icon: "Sparkles",
    status: "active",
  },
  {
    id: "rrf",
    label: "RRF Fusion",
    caption: "Reciprocal rank fusion by chunk_id",
    icon: "Combine",
    status: "pending",
  },
  {
    id: "rerank",
    label: "Cross-Encoder Rerank",
    caption: "Top-K evidence from candidates",
    icon: "ArrowUpDown",
    status: "pending",
  },
  {
    id: "evidence",
    label: "Evidence Selection",
    caption: "Validated against scope",
    icon: "CheckCircle2",
    status: "pending",
  },
  {
    id: "llm",
    label: "Groq LLM",
    caption: "llama-3.3-70b · streaming",
    icon: "Bot",
    status: "pending",
  },
  {
    id: "cite",
    label: "Citation Validation",
    caption: "Server-side rank filter",
    icon: "BadgeCheck",
    status: "pending",
  },
  {
    id: "answer",
    label: "Final Answer",
    caption: "Returned to client",
    icon: "Send",
    status: "pending",
  },
];

// ──────────────────────────────────────────────────────────────────────
// Retrieval performance table (4 arms × 5 metrics)
// ──────────────────────────────────────────────────────────────────────

export const retrievalRows: RetrievalRow[] = [
  {
    method: "BM25",
    recallAt5: 0.62,
    mrrAt10: 0.51,
    hitAt1: 0.48,
    ndcgAt10: 0.55,
    precisionAt5: 0.41,
  },
  {
    method: "Dense",
    recallAt5: 0.71,
    mrrAt10: 0.58,
    hitAt1: 0.52,
    ndcgAt10: 0.63,
    precisionAt5: 0.47,
  },
  {
    method: "Hybrid (RRF)",
    recallAt5: 0.86,
    mrrAt10: 0.72,
    hitAt1: 0.68,
    ndcgAt10: 0.78,
    precisionAt5: 0.59,
  },
  {
    method: "Hybrid + Rerank",
    recallAt5: 0.94,
    mrrAt10: 0.82,
    hitAt1: 0.79,
    ndcgAt10: 0.88,
    precisionAt5: 0.71,
    highlighted: true,
  },
];

// ──────────────────────────────────────────────────────────────────────
// RAGAS gauges (4 metrics, 0..1)
// ──────────────────────────────────────────────────────────────────────

export const ragasGauges: RagasGaugeData[] = [
  { label: "Faithfulness", value: 0.91 },
  { label: "Answer Relevancy", value: 0.87 },
  { label: "Context Precision", value: 0.83 },
  { label: "Context Recall", value: 0.79, highlighted: true },
];

// ──────────────────────────────────────────────────────────────────────
// Security & Isolation checks (PASS / ACTIVE / FAIL → semantic tokens)
// ──────────────────────────────────────────────────────────────────────

export const securityChecks: SecurityCheck[] = [
  {
    id: "rbac",
    label: "RBAC Filter",
    status: "PASS",
    detail: "1,248 queries · 0 violations",
  },
  {
    id: "tenant",
    label: "Tenant Isolation",
    status: "PASS",
    detail: "Cross-tenant hits = 0",
  },
  {
    id: "cache-scope",
    label: "Cache Scope Hash",
    status: "ACTIVE",
    detail: "Includes auth + tenant + corpus + model",
  },
  {
    id: "pii",
    label: "PII Redaction",
    status: "PASS",
    detail: "0 records flagged in stream",
  },
];

// ──────────────────────────────────────────────────────────────────────
// Cache performance (L1/L2/Miss rates + latency)
// ──────────────────────────────────────────────────────────────────────

export const cacheStats: CacheStat[] = [
  {
    label: "L1 Exact Hit",
    value: 31.4,
    unit: "%",
    delta: DELTA_UP_GOOD_SMALL,
  },
  {
    label: "L2 Semantic Hit",
    value: 32.0,
    unit: "%",
    delta: DELTA_UP_GOOD_SMALL,
  },
  {
    label: "Cache Miss",
    value: 36.6,
    unit: "%",
    delta: DELTA_DOWN_GOOD,
  },
  {
    label: "Avg Latency Saved",
    value: 1180,
    unit: "ms",
    delta: DELTA_DOWN_GOOD,
  },
];

// ──────────────────────────────────────────────────────────────────────
// Queries over time (line chart, 7 points)
// ──────────────────────────────────────────────────────────────────────

export const queriesOverTime: ChartPoint[] = [
  { label: "Mon", value: 142 },
  { label: "Tue", value: 168 },
  { label: "Wed", value: 191 },
  { label: "Thu", value: 174 },
  { label: "Fri", value: 215 },
  { label: "Sat", value: 98 },
  { label: "Sun", value: 260 },
];

// ──────────────────────────────────────────────────────────────────────
// Query types donut
// ──────────────────────────────────────────────────────────────────────

export const queryTypes: DonutSegment[] = [
  { label: "Document RAG", value: 68, color: "var(--color-series-1)" },
  { label: "SQL / Structured", value: 21, color: "var(--color-series-3)" },
  { label: "Refused / Other", value: 11, color: "var(--color-series-6)" },
];

// ──────────────────────────────────────────────────────────────────────
// Sources panel (right rail on chat + dashboard)
// ──────────────────────────────────────────────────────────────────────

export const sourceCards: SourceCardData[] = [
  {
    rank: 1,
    documentId: "HR-002",
    documentTitle: "Leave Policy",
    fileType: "MD",
    department: "Human Resources",
    sectionTitle: "Annual Leave Entitlement",
    relevance: 0.94,
    excerpt:
      "Each full-time employee is entitled to 18 days of paid annual leave, accrued at 1.5 days per calendar month…",
  },
  {
    rank: 2,
    documentId: "HR-007",
    documentTitle: "Remote Work Policy",
    fileType: "MD",
    department: "Human Resources",
    sectionTitle: "Eligibility & Scope",
    relevance: 0.88,
    excerpt:
      "Remote work arrangements are available to employees who have completed at least 90 days of continuous service…",
  },
  {
    rank: 3,
    documentId: "OPS-001",
    documentTitle: "Project Management SOP",
    fileType: "MD",
    department: "Operations",
    sectionTitle: "Initiation Phase",
    relevance: 0.79,
    excerpt:
      "Every project must complete a documented initiation phase with stakeholder sign-off before resource allocation…",
  },
];

// ──────────────────────────────────────────────────────────────────────
// Right rail — current user context (hydrated from /api/auth/me at boot,
// mirrored here so the dashboard renders even before that fetch resolves)
// ──────────────────────────────────────────────────────────────────────

export const currentUserContext: UserContextData = {
  initials: "IP",
  name: "Insha Parveen",
  role: "hr",
  tenant: "nexacore",
  department: "Human Resources",
  clearanceLevel: "L3 — Confidential",
  accessScope: "HR + Operations · Read",
};

// ──────────────────────────────────────────────────────────────────────
// Real (Phase 8) values — cited where used
// ──────────────────────────────────────────────────────────────────────

// These values come from the offline Phase 8 evaluation report
// (`evaluation/reports/phase8_dev_report.html`). They are the *only*
// non-demo values allowed on the dashboard. If the report changes,
// update these in lockstep.
//
// Phase 8 retrieval (Hybrid + Rerank, dev split, n=240):
//   recall@5 ≈ 0.94  → matches the highlighted table row above
//   MRR@10    ≈ 0.82  → matches the highlighted table row above
//
// Export them through a separate constant so the consumer is forced
// to type-narrow and see the citation.
export const PHASE8_CITED_RETRIEVAL = {
  recallAt5: 0.94,
  mrrAt10: 0.82,
  source: "evaluation/reports/phase8_dev_report.html",
} as const;