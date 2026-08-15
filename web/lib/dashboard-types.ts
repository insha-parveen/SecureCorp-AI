// Types used by the dashboard. Mirrors the shape of real backend
// payloads (where applicable) and adds dashboard-only shapes for the
// mock panels.

export type Direction = "up" | "down" | "flat";
export type Tone = "good" | "bad" | "neutral";

export interface KpiDelta {
  /** Signed change vs the previous comparable period (e.g., last 7 days). */
  value: number;
  /** Percent form of the delta ("+18.6%"). */
  percent: number;
  direction: Direction;
  tone: Tone;
}

export interface StatTileData {
  label: string;
  value: string;
  rawValue: number;
  delta?: KpiDelta;
  sparkline?: number[];
  /** "var(--color-series-N)" or one of the semantic tokens. */
  accent?: string;
  icon?: string;
}

export interface PipelineStep {
  id: string;
  label: string;
  caption: string;
  /** lucide icon name (resolved at render). */
  icon: string;
  status: "done" | "active" | "pending";
  /** Optional 1-2 line subtitle (e.g., "Top 50 results"). */
  meta?: string;
}

export interface RetrievalRow {
  method: "BM25" | "Dense" | "Hybrid (RRF)" | "Hybrid + Rerank";
  recallAt5: number;
  mrrAt10: number;
  hitAt1: number;
  ndcgAt10: number;
  precisionAt5: number;
  highlighted?: boolean;
}

export interface RagasGaugeData {
  label: string;
  value: number; // 0..1
  highlighted?: boolean;
}

export interface SecurityCheck {
  id: string;
  label: string;
  status: "PASS" | "ACTIVE" | "FAIL";
  detail: string;
}

export interface CacheStat {
  label: string;
  value: number; // percent (e.g., 42) or ms (e.g., 120)
  unit: "%" | "ms";
  delta?: KpiDelta;
}

export interface SourceCardData {
  rank: number;
  documentId: string;
  documentTitle: string;
  fileType: "PDF" | "DOCX" | "MD" | "TXT";
  department: string;
  sectionTitle: string;
  relevance: number; // 0..1
  excerpt: string;
}

export interface UserContextData {
  initials: string;
  name: string;
  role: string;
  tenant: string;
  department: string;
  clearanceLevel: string;
  accessScope: string;
}

export interface DonutSegment {
  label: string;
  value: number; // percent 0..100
  /** CSS color (use var(--color-series-N)). */
  color: string;
}

export interface ChartPoint {
  label: string;
  value: number;
}
