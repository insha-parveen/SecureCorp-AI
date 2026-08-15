// Shared TypeScript shapes. Mirror the FastAPI response models — the
// frontend is the only other consumer of these contracts, and changing
// the wire format means changing both sides in the same commit.

export type Role = string; // role values are free-form on the server

export interface User {
  user_id: string;
  roles: Role[];
  department: string | null;
  tenant_id: string;
  expires_in: number;
}

export interface RankedEvidence {
  rank: number;
  chunk_id: string;
  document_id: string;
  document_title: string;
  section_title: string | null;
  excerpt: string;
}

export interface DonePayload {
  answer: string;
  citations: number[]; // ranks into `evidence`
  evidence: RankedEvidence[];
  model: string;
  usage: Record<string, number>;
  extras: Record<string, unknown>;
}

// Pipeline telemetry, emitted before evidence. `route` is null on a cache
// hit (routing was skipped). `cache_tier` is "L1" | "L2" | "MISS".
export interface MetaPayload {
  route: "DOCUMENT_RAG" | "STRUCTURED_SQL" | "REFUSE" | null;
  cache_tier: "L1" | "L2" | "MISS";
}

// The SSE event shapes the chat route emits. The `data` payload is
// already JSON-parsed by the SSE client before reaching the hook.
export type ChatEvent =
  | { event: "meta"; data: MetaPayload }
  | { event: "evidence"; data: RankedEvidence }
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: DonePayload }
  | { event: "error"; data: { message: string; type: string } };

// The shape that the chat UI actually renders. Built incrementally by the
// streaming hook as SSE events arrive.
export interface AssistantMessage {
  meta: MetaPayload | null;
  evidence: RankedEvidence[];
  text: string;
  done: DonePayload | null;
  error: { message: string; type: string } | null;
}

export interface UserMessage {
  text: string;
}

export type Message = { role: "user"; content: UserMessage } | { role: "assistant"; content: AssistantMessage };
