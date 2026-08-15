// Pipeline state model + pure reducer: SSE stream -> per-node status.
//
// This is the SINGLE source of pipeline logic (no duplication across
// pages). It is deliberately React-free and pure so it can be unit
// tested exhaustively and reused by both the live /chat pipeline and the
// static landing-page showcase.
//
// TRUTHFULNESS CONTRACT (CLAUDE.md §26.3): every status this reducer
// reports is something the backend actually told us. It reports only the
// checkpoints we can prove from the stream:
//
//   - a request is in flight            -> auth is being established
//   - a `meta` event arrived            -> auth+authz+routing succeeded
//                                          (routing runs AFTER both), and
//                                          we know the branch + cache tier
//   - `evidence` arrived (RAG)          -> retrieval completed
//   - `token`s arrived (RAG)            -> generation is producing text
//   - `done` arrived                    -> the whole path completed
//   - `error` arrived                   -> the active node failed
//
// The component layer (securecorp-pipeline) may add a time-based cursor
// that walks the *already-completed* prefix so the user sees nodes light
// up one-by-one, but it must never show a node as completed that this
// reducer reports as idle/failed. Animation is embellishment bounded by
// truth.

import type { AssistantMessage, ChatEvent, MetaPayload, RankedEvidence, User } from "./types";

export type NodeStatus = "idle" | "processing" | "completed" | "failed";
export type RouteState = "DOCUMENT_RAG" | "STRUCTURED_SQL" | "REFUSE";
export type CacheTier = "L1" | "L2" | "MISS";

// The fixed pipeline topology. These ids are the contract between the
// reducer, the graph component, and the detail popovers.
export type PipelineNodeId =
  | "user"
  | "auth"
  | "authz"
  | "semantic_cache"
  | "router"
  | "doc_rag"
  | "structured_sql"
  | "refuse"
  | "generation"
  | "citation"
  | "response";

// Canonical render order for the full graph (branches included). The
// component positions these; the reducer only assigns statuses.
export const PIPELINE_NODE_IDS: readonly PipelineNodeId[] = [
  "user",
  "auth",
  "authz",
  "semantic_cache",
  "router",
  "doc_rag",
  "structured_sql",
  "refuse",
  "generation",
  "citation",
  "response",
] as const;

export interface PipelineState {
  /** The classified route, or null before `meta` / on a cache hit. */
  route: RouteState | null;
  /** L1 / L2 / MISS once known, else null. */
  cacheTier: CacheTier | null;
  /** True when the answer was served from cache (L1/L2). */
  cacheHit: boolean;
  /** The node currently processing (the moving cursor target), or null. */
  activeNodeId: PipelineNodeId | null;
  /** Authoritative status for every node in the graph. */
  statuses: Record<PipelineNodeId, NodeStatus>;
  /** The ordered node ids on the path actually taken (for the connectors). */
  path: PipelineNodeId[];
  // Convenience pass-throughs for the detail popovers (real values only).
  evidence: RankedEvidence[];
  citations: number[];
  model: string | null;
}

function allIdle(): Record<PipelineNodeId, NodeStatus> {
  return {
    user: "idle",
    auth: "idle",
    authz: "idle",
    semantic_cache: "idle",
    router: "idle",
    doc_rag: "idle",
    structured_sql: "idle",
    refuse: "idle",
    generation: "idle",
    citation: "idle",
    response: "idle",
  };
}

/** The ordered nodes on the path for a given route / cache scenario. */
function pathFor(route: RouteState | null, cacheHit: boolean): PipelineNodeId[] {
  if (cacheHit) {
    // Cache hit: auth+authz scoping happens in the cache lookup; router,
    // retrieval, and generation are genuinely SKIPPED. Off-path nodes stay
    // idle (dimmed) so the viz never implies retrieval ran.
    return ["user", "auth", "authz", "semantic_cache", "response"];
  }
  switch (route) {
    case "REFUSE":
      return ["user", "auth", "authz", "semantic_cache", "router", "refuse", "response"];
    case "STRUCTURED_SQL":
      return ["user", "auth", "authz", "semantic_cache", "router", "structured_sql", "generation", "citation", "response"];
    case "DOCUMENT_RAG":
      return ["user", "auth", "authz", "semantic_cache", "router", "doc_rag", "generation", "citation", "response"];
    default:
      // No meta yet: we only know a request is in flight and that auth +
      // authz precede routing.
      return ["user", "auth", "authz", "semantic_cache", "router"];
  }
}

/**
 * Pick the node currently being processed, given the strongest signal in
 * the message. Assumes the request is streaming and not yet done/errored.
 */
function activeNodeFor(
  message: AssistantMessage,
  route: RouteState | null,
  cacheHit: boolean,
): PipelineNodeId {
  const hasEvidence = message.evidence.length > 0;
  const hasTokens = message.text.length > 0;

  if (cacheHit) return "response"; // cached answer about to be emitted
  if (route === null) return "auth"; // pre-meta: auth/authz/routing in flight

  if (route === "REFUSE") return "refuse";

  if (route === "STRUCTURED_SQL") {
    // SQL path does not stream tokens; structured_sql runs, then generation
    // turns the rows into prose. Evidence never arrives on this path.
    return "structured_sql";
  }

  // DOCUMENT_RAG
  if (hasTokens) return "generation"; // generation is producing text
  if (hasEvidence) return "generation"; // retrieval done, generation starting
  return "doc_rag"; // still retrieving
}

/**
 * Derive the authoritative pipeline state from the accumulated assistant
 * message and the streaming flag. Pure and deterministic.
 *
 * @param message the accumulated assistant message, or null before submit.
 * @param isStreaming whether a request is currently in flight.
 */
export function derivePipelineState(
  message: AssistantMessage | null,
  isStreaming: boolean,
): PipelineState {
  const meta: MetaPayload | null = message?.meta ?? null;
  const route = (meta?.route ?? null) as RouteState | null;
  const cacheTier = (meta?.cache_tier ?? null) as CacheTier | null;
  const cacheHit = cacheTier === "L1" || cacheTier === "L2";

  const evidence = message?.evidence ?? [];
  const citations = message?.done?.citations ?? [];
  const model = message?.done?.model ?? null;

  const path = pathFor(route, cacheHit);
  const statuses = allIdle();

  // No request yet: everything idle.
  if (message === null) {
    return {
      route,
      cacheTier,
      cacheHit,
      activeNodeId: null,
      statuses,
      path,
      evidence,
      citations,
      model,
    };
  }

  const isDone = message.done !== null;
  const hasError = message.error !== null;

  if (isDone) {
    // Terminal success: every node on the path completed.
    for (const id of path) statuses[id] = "completed";
    return {
      route,
      cacheTier,
      cacheHit,
      activeNodeId: null,
      statuses,
      path,
      evidence,
      citations,
      model,
    };
  }

  // Determine the node currently in progress (the cursor target).
  const active = activeNodeFor(message, route, cacheHit);
  const activeIdx = path.indexOf(active);

  for (let i = 0; i < path.length; i++) {
    const id = path[i];
    if (i < activeIdx) statuses[id] = "completed";
    else if (i === activeIdx) statuses[id] = hasError ? "failed" : "processing";
    else statuses[id] = "idle";
  }

  return {
    route,
    cacheTier,
    cacheHit,
    // A failed node is not an animation target.
    activeNodeId: hasError ? null : active,
    statuses,
    path,
    evidence,
    citations,
    model,
  };
}

/**
 * Fold a list of raw SSE events into an AssistantMessage, mirroring the
 * accumulation the streaming hook performs. Lets tests (and the static
 * showcase) express scenarios as event lists.
 */
export function messageFromEvents(events: ChatEvent[]): AssistantMessage {
  const message: AssistantMessage = {
    meta: null,
    evidence: [],
    text: "",
    done: null,
    error: null,
  };
  for (const ev of events) {
    switch (ev.event) {
      case "meta":
        message.meta = ev.data;
        break;
      case "evidence":
        message.evidence.push(ev.data);
        break;
      case "token":
        message.text += ev.data.text;
        break;
      case "done":
        message.done = ev.data;
        break;
      case "error":
        message.error = ev.data;
        break;
    }
  }
  return message;
}

/**
 * Convenience: derive pipeline state directly from a list of SSE events.
 * `isStreaming` defaults to "not done and no error" so a partial event
 * list reads as an in-flight request.
 */
export function pipelineStateFromEvents(
  events: ChatEvent[],
  isStreaming?: boolean,
): PipelineState {
  const message = messageFromEvents(events);
  const streaming = isStreaming ?? (message.done === null && message.error === null);
  return derivePipelineState(message, streaming);
}

// -- node detail (for the click/keyboard popover) ----------------------
//
// The literal string every unavailable field falls back to. Using one
// constant keeps the "never invent data" rule greppable and testable.
export const NOT_AVAILABLE = "Not available";

export interface DetailRow {
  label: string;
  value: string;
}

export interface NodeDetail {
  title: string;
  /** One-line description of what this stage does. */
  description: string;
  rows: DetailRow[];
}

/**
 * Build the detail rows for a node using ONLY real values from the
 * verified user context and the request state. Anything not on the wire
 * is reported as {@link NOT_AVAILABLE}; nothing is invented.
 *
 * `user` is the JWT-verified UserContext from /api/auth/me (never the
 * request body). Passing null (logged-out preview) yields NOT_AVAILABLE
 * for the identity rows rather than fabricated names.
 */
export function nodeDetail(
  id: PipelineNodeId,
  state: PipelineState,
  user: User | null,
): NodeDetail {
  const na = NOT_AVAILABLE;
  switch (id) {
    case "user":
      return {
        title: "User",
        description: "The authenticated caller who submitted the query.",
        rows: [{ label: "User ID", value: user?.user_id ?? na }],
      };
    case "auth":
      return {
        title: "Authentication",
        description: "JWT verified server-side; identity built from the token, never the request body.",
        rows: [
          { label: "Method", value: "JWT (httpOnly cookie)" },
          { label: "User ID", value: user?.user_id ?? na },
          {
            label: "Session valid for",
            value: user ? `${user.expires_in}s` : na,
          },
        ],
      };
    case "authz":
      return {
        title: "Authorization",
        description: "RBAC + ABAC and tenant isolation applied BEFORE retrieval / SQL / generation.",
        rows: [
          { label: "Status", value: user ? "Authorized" : na },
          { label: "Roles", value: user?.roles.length ? user.roles.join(", ") : na },
          { label: "Department", value: user?.department ?? na },
          { label: "Tenant", value: user?.tenant_id ?? na },
        ],
      };
    case "semantic_cache":
      return {
        title: "Semantic Cache",
        description: "Authorization-scoped L1 (exact) and L2 (semantic) cache lookup. A hit skips routing, retrieval, and generation.",
        rows: [
          { label: "Cache tier", value: state.cacheTier ?? na },
          { label: "Result", value: state.cacheHit ? "Hit — served from cache" : "Miss — full path runs" },
        ],
      };
    case "router":
      return {
        title: "Query Router",
        description: "Classifies the query into DOCUMENT_RAG, STRUCTURED_SQL, or REFUSE.",
        rows: [
          { label: "Route", value: state.route ?? (state.cacheHit ? "Skipped (cache hit)" : na) },
          { label: "Cache tier", value: state.cacheTier ?? na },
        ],
      };
    case "doc_rag":
      return {
        title: "Document RAG",
        description: "Hybrid retrieval: BM25 + Dense → RRF → cross-encoder rerank → top-K evidence.",
        rows: [
          { label: "Method", value: "BM25 + Dense (RRF) + Reranker" },
          {
            label: "Top-K evidence",
            value: state.evidence.length > 0 ? String(state.evidence.length) : na,
          },
          // Candidate/reranked counts are not on the SSE wire — do not invent.
          { label: "Candidates", value: na },
          { label: "Reranked", value: na },
        ],
      };
    case "structured_sql":
      return {
        title: "Structured SQL",
        description: "Template-based SQL over PostgreSQL with tenant + RBAC enforced at the data boundary.",
        rows: [
          { label: "Database", value: "PostgreSQL" },
          { label: "Authorization", value: state.route === "STRUCTURED_SQL" ? "Passed" : na },
          { label: "Tenant isolation", value: state.route === "STRUCTURED_SQL" ? "Active" : na },
          {
            label: "Result",
            value: state.route === "STRUCTURED_SQL" && state.statuses.response === "completed" ? "Available" : na,
          },
          // Raw SQL is intentionally not exposed to the client.
          { label: "SQL", value: na },
        ],
      };
    case "refuse":
      return {
        title: "Refuse / Out-of-scope",
        description: "The router judged the query out-of-scope; a safe refusal is returned.",
        rows: [
          { label: "Route", value: state.route === "REFUSE" ? "REFUSE" : na },
          { label: "Retrieval", value: "Not performed" },
        ],
      };
    case "generation":
      return {
        title: "Generation",
        description: "Groq LLM answers using ONLY the authorized evidence/context.",
        rows: [
          { label: "Model", value: state.model ?? na },
          { label: "Context", value: "Authorized evidence only" },
        ],
      };
    case "citation":
      return {
        title: "Citation Validation",
        description: "Every cited ID is validated server-side against the retrieved evidence.",
        rows: [
          {
            label: "Citations",
            value: state.citations.length > 0 ? state.citations.map((c) => `[${c}]`).join(" ") : na,
          },
          {
            label: "Evidence verified",
            value: state.evidence.length > 0 ? String(state.evidence.length) : na,
          },
        ],
      };
    case "response":
      return {
        title: "Final Response",
        description: "The validated answer plus its resolved citations.",
        rows: [
          { label: "Cache tier", value: state.cacheTier ?? na },
          {
            label: "Citations",
            value: state.citations.length > 0 ? String(state.citations.length) : na,
          },
        ],
      };
  }
}
