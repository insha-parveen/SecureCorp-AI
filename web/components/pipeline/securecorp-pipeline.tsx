"use client";

// SecureCorpPipeline — the compact, technically-accurate visualization of
// the ACTUAL request pipeline (CLAUDE.md §26). Not a dashboard, not a
// decorative poster.
//
//   USER → AUTH → AUTHZ → ROUTER ──┬── DOCUMENT RAG ──┐
//                                  ├── STRUCTURED SQL ─┤→ GENERATION → CITATION → RESPONSE
//                                  └── REFUSE ─────────────────────────────────→ (safe response)
//
// Layout: a vertical spine (USER→ROUTER), a 3-way branch row, then a
// rejoin spine (GENERATION→CITATION→RESPONSE). On desktop the branch row
// is three columns; on mobile it stacks. It never scrolls horizontally
// forever — the branch row wraps.
//
// Truthfulness: node STATUS comes entirely from derivePipelineState (the
// pure reducer). The only thing this component adds is a time-based
// cursor that reveals the already-completed prefix one node at a time
// while streaming, so the user perceives motion — it can never mark a
// node completed that the reducer left idle/failed. prefers-reduced-motion
// disables the cursor and shows the final truthful state immediately.

import * as React from "react";
import { useReducedMotion } from "motion/react";
import { ChevronDown } from "lucide-react";
import {
  derivePipelineState,
  nodeDetail,
  type NodeStatus,
  type PipelineNodeId,
  type PipelineState,
} from "@/lib/pipeline-state";
import type { AssistantMessage, User } from "@/lib/types";
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardTitle,
} from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { SecureCorpPipelineNode, type NodeAccent } from "./securecorp-pipeline-node";
import { PipelineDetail } from "./pipeline-detail";

// Static per-node presentation. Status is injected at render time.
interface NodeMeta {
  id: PipelineNodeId;
  label: string;
  lines: string[];
  icon: string;
  accent: NodeAccent;
}

const SPINE_TOP: NodeMeta[] = [
  { id: "user", label: "User", lines: ["Query"], icon: "User", accent: "neutral" },
  { id: "auth", label: "Authentication", lines: ["JWT", "UserContext"], icon: "KeyRound", accent: "neutral" },
  { id: "authz", label: "Authorization", lines: ["RBAC / ABAC", "Tenant isolation"], icon: "ShieldCheck", accent: "neutral" },
  { id: "router", label: "Query Router", lines: ["RAG · SQL · Refuse"], icon: "GitBranch", accent: "neutral" },
];

const BRANCHES: NodeMeta[] = [
  { id: "doc_rag", label: "Document RAG", lines: ["BM25 + Dense", "RRF · Reranker", "Top-K evidence"], icon: "Search", accent: "rag" },
  { id: "structured_sql", label: "Structured SQL", lines: ["PostgreSQL", "Authz filter", "Query results"], icon: "Database", accent: "sql" },
  { id: "refuse", label: "Refuse", lines: ["Out-of-scope", "Safe response"], icon: "ShieldX", accent: "refuse" },
];

const SPINE_BOTTOM: NodeMeta[] = [
  { id: "generation", label: "Generation", lines: ["Groq LLM", "Authorized context"], icon: "Sparkles", accent: "generation" },
  { id: "citation", label: "Citation Validation", lines: ["Validate citations", "Evidence verify"], icon: "BadgeCheck", accent: "generation" },
  { id: "response", label: "Final Response", lines: ["Answer", "Citations"], icon: "MessageSquareText", accent: "neutral" },
];

export interface SecureCorpPipelineProps {
  /** The accumulated assistant message (live). Null renders the idle graph. */
  message?: AssistantMessage | null;
  /** Whether a request is in flight. */
  isStreaming?: boolean;
  /** JWT-verified user for the auth/authz detail rows. */
  user?: User | null;
  /** Header label. */
  title?: string;
  className?: string;
}

// How long the reveal cursor dwells on each node while streaming.
const CURSOR_INTERVAL_MS = 420;

export function SecureCorpPipeline({
  message = null,
  isStreaming = false,
  user = null,
  title = "How this answer was generated",
  className,
}: SecureCorpPipelineProps) {
  const reducedMotion = useReducedMotion();

  // The authoritative state (pure). Everything below only *reveals* this.
  const state = React.useMemo(
    () => derivePipelineState(message, isStreaming),
    [message, isStreaming],
  );

  // Time-based reveal cursor: walk the path's completed/processing prefix
  // one node at a time so motion is visible. Bounded by `revealMax` — the
  // furthest node the reducer says we've legitimately reached.
  const revealMax = furthestReached(state);
  const [revealIdx, setRevealIdx] = React.useState(revealMax);

  React.useEffect(() => {
    if (reducedMotion || !isStreaming) {
      setRevealIdx(revealMax);
      return;
    }
    // Advance toward revealMax; never past it.
    setRevealIdx((prev) => Math.min(prev, revealMax));
    const timer = window.setInterval(() => {
      setRevealIdx((prev) => (prev >= revealMax ? prev : prev + 1));
    }, CURSOR_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [revealMax, isStreaming, reducedMotion]);

  // When not streaming, always show the full truthful state.
  const effectiveReveal = isStreaming && !reducedMotion ? revealIdx : revealMax;

  // Compute the displayed status for a node: clamp the reducer's status by
  // the reveal cursor so not-yet-revealed on-path nodes read as idle.
  const displayStatus = React.useCallback(
    (id: PipelineNodeId): NodeStatus => {
      const truth = state.statuses[id];
      if (truth === "idle" || truth === "failed") return truth;
      const posInPath = state.path.indexOf(id);
      if (posInPath === -1) return truth;
      if (posInPath > effectiveReveal) return "idle"; // not revealed yet
      if (posInPath === effectiveReveal && isStreaming) {
        // The cursor's leading edge shows as processing while streaming.
        return truth === "completed" && posInPath < revealMax ? "completed" : "processing";
      }
      return truth;
    },
    [state, effectiveReveal, isStreaming, revealMax],
  );

  const [openNode, setOpenNode] = React.useState<PipelineNodeId | null>(null);
  const toggle = (id: PipelineNodeId) => setOpenNode((cur) => (cur === id ? null : id));

  const renderNode = (meta: NodeMeta) => {
    const detailId = `pipe-detail-${meta.id}`;
    return (
      <div className="relative">
        <SecureCorpPipelineNode
          label={meta.label}
          lines={meta.lines}
          icon={meta.icon}
          accent={meta.accent}
          status={displayStatus(meta.id)}
          expanded={openNode === meta.id}
          onActivate={() => toggle(meta.id)}
        />
        {openNode === meta.id ? (
          <div className="absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2">
            <PipelineDetail
              id={detailId}
              detail={nodeDetail(meta.id, state, user)}
              onClose={() => setOpenNode(null)}
            />
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <GlassCard className={className}>
      <GlassCardHeader className="flex-row items-center justify-between space-y-0">
        <GlassCardTitle>{title}</GlassCardTitle>
        <PipelineStatusBadge state={state} isStreaming={isStreaming} />
      </GlassCardHeader>
      <GlassCardContent>
        <ol
          className="flex flex-col items-center gap-2"
          aria-label="SecureCorp request pipeline"
        >
          {/* Spine: USER → AUTH → AUTHZ → ROUTER */}
          {SPINE_TOP.map((meta) => (
            <li key={meta.id} className="contents">
              {renderNode(meta)}
              {/* The router fans out via BranchFanOut instead of a plain
                  connector; every other spine node keeps its connector. */}
              {meta.id !== "router" ? (
                <Connector active={isBelowRevealed(state, meta.id, effectiveReveal)} />
              ) : null}
            </li>
          ))}

          {/* Decision fan-out: ROUTER → { DOCUMENT RAG | STRUCTURED SQL | REFUSE }.
              Only the taken branch's leg lights; the bus lights once routing
              is decided. This is the visible "decision" the router makes. */}
          <li className="w-full">
            <BranchFanOut
              routerReached={isReached(state, "router", effectiveReveal)}
              branchActive={(id) => isActive(displayStatus(id))}
            />
          </li>

          {/* Branch row: DOCUMENT RAG | STRUCTURED SQL | REFUSE */}
          <li className="w-full">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {BRANCHES.map((meta) => (
                <div key={meta.id} className="flex justify-center">
                  {renderNode(meta)}
                </div>
              ))}
            </div>
          </li>

          {/* Fan-in: RAG / SQL → GENERATION. REFUSE does not rejoin — it
              terminates at the final response, which the fan-in states. */}
          <li className="w-full">
            <BranchFanIn
              route={state.route}
              ragActive={isActive(displayStatus("doc_rag"))}
              sqlActive={isActive(displayStatus("structured_sql"))}
              generationReached={isActive(displayStatus("generation"))}
            />
          </li>

          {/* Spine: GENERATION → CITATION → RESPONSE */}
          {SPINE_BOTTOM.map((meta, i) => (
            <li key={meta.id} className="contents">
              {renderNode(meta)}
              {i < SPINE_BOTTOM.length - 1 ? (
                <Connector active={isBelowRevealed(state, meta.id, effectiveReveal)} />
              ) : null}
            </li>
          ))}
        </ol>

        <p className="mt-3 text-center text-[10px] text-[var(--color-muted-foreground)]">
          Authorization is enforced before retrieval, SQL, and generation.
        </p>
      </GlassCardContent>
    </GlassCard>
  );
}

// -- helpers -----------------------------------------------------------

/** Index in the path of the furthest node the reducer legitimately reached. */
function furthestReached(state: PipelineState): number {
  let max = -1;
  for (let i = 0; i < state.path.length; i++) {
    const s = state.statuses[state.path[i]];
    if (s === "completed" || s === "processing" || s === "failed") max = i;
  }
  return max;
}

/** Whether the connector below `id` should be lit (id is revealed & on-path). */
function isBelowRevealed(state: PipelineState, id: PipelineNodeId, reveal: number): boolean {
  const idx = state.path.indexOf(id);
  return idx !== -1 && idx < reveal;
}

/** Whether a node has been reached by the reveal cursor (at or before it). */
function isReached(state: PipelineState, id: PipelineNodeId, reveal: number): boolean {
  const idx = state.path.indexOf(id);
  return idx !== -1 && idx <= reveal;
}

/** A node is "active" (lit) once it is processing or completed. */
function isActive(status: NodeStatus): boolean {
  return status === "processing" || status === "completed";
}

// Horizontal centers of the three branch columns (grid-cols-3, centered
// nodes). Shared by the fan-out and fan-in so their legs line up.
const BRANCH_X = { doc_rag: "16.666%", structured_sql: "50%", refuse: "83.333%" } as const;
const BRANCH_ACCENT = {
  doc_rag: "var(--color-success)",
  structured_sql: "var(--color-series-1)",
  refuse: "var(--color-critical)",
} as const;

/**
 * The decision fan-out: a stub down from the router, a horizontal bus, and
 * three legs with arrowheads into each branch column. Only the taken branch's
 * leg lights (its node is the only one that leaves idle); the bus lights once
 * routing is decided. Pure presentation — no motion of its own, so it reads
 * correctly under prefers-reduced-motion.
 */
function BranchFanOut({
  routerReached,
  branchActive,
}: {
  routerReached: boolean;
  branchActive: (id: PipelineNodeId) => boolean;
}) {
  const busColor = routerReached ? "var(--color-primary)" : "var(--color-border)";
  const busOpacity = routerReached ? 0.9 : 0.5;
  const legs = ["doc_rag", "structured_sql", "refuse"] as const;
  return (
    <div aria-hidden>
      {/* Desktop bracket */}
      <div className="relative mx-auto hidden h-12 w-full sm:block">
        <span
          className="absolute left-1/2 top-0 h-3 w-px -translate-x-1/2"
          style={{ backgroundColor: busColor, opacity: busOpacity }}
        />
        <span
          className="absolute top-3 h-px"
          style={{ left: BRANCH_X.doc_rag, right: BRANCH_X.doc_rag, backgroundColor: busColor, opacity: busOpacity }}
        />
        {legs.map((id) => {
          const active = branchActive(id);
          const color = active ? BRANCH_ACCENT[id] : "var(--color-border)";
          return (
            <React.Fragment key={id}>
              <span
                className="absolute top-3 h-6 w-px -translate-x-1/2"
                style={{ left: BRANCH_X[id], backgroundColor: color, opacity: active ? 0.9 : 0.5 }}
              />
              <ChevronDown
                size={14}
                className="absolute -translate-x-1/2"
                style={{ left: BRANCH_X[id], top: "32px", color, opacity: active ? 1 : 0.5 }}
              />
            </React.Fragment>
          );
        })}
      </div>
      {/* Mobile: a single connector into the stacked branch list */}
      <div className="flex h-4 items-center justify-center sm:hidden">
        <span className="h-full w-px" style={{ backgroundColor: busColor, opacity: busOpacity }} />
      </div>
    </div>
  );
}

/**
 * The fan-in: RAG and SQL legs converge to a bus and down into generation.
 * REFUSE is deliberately absent here — on a REFUSE run it terminates at the
 * final response with no generation, which we state explicitly so the flow
 * is never ambiguous.
 */
function BranchFanIn({
  route,
  ragActive,
  sqlActive,
  generationReached,
}: {
  route: PipelineState["route"];
  ragActive: boolean;
  sqlActive: boolean;
  generationReached: boolean;
}) {
  if (route === "REFUSE") {
    return (
      <div aria-hidden className="py-1 text-center">
        <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--color-critical)] opacity-80">
          Refuse → final response · no generation
        </span>
      </div>
    );
  }
  const genColor = generationReached ? "var(--color-accent-violet)" : "var(--color-border)";
  const busLit = ragActive || sqlActive;
  return (
    <div aria-hidden>
      <div className="relative mx-auto hidden h-12 w-full sm:block">
        {/* Legs down from RAG (1/6) and SQL (1/2) to the bus. */}
        <span
          className="absolute top-0 h-6 w-px -translate-x-1/2"
          style={{ left: BRANCH_X.doc_rag, backgroundColor: ragActive ? BRANCH_ACCENT.doc_rag : "var(--color-border)", opacity: ragActive ? 0.9 : 0.5 }}
        />
        <span
          className="absolute top-0 h-6 w-px -translate-x-1/2"
          style={{ left: BRANCH_X.structured_sql, backgroundColor: sqlActive ? BRANCH_ACCENT.structured_sql : "var(--color-border)", opacity: sqlActive ? 0.9 : 0.5 }}
        />
        {/* Bus from RAG center to generation center. */}
        <span
          className="absolute h-px"
          style={{ left: BRANCH_X.doc_rag, width: "33.333%", top: "24px", backgroundColor: busLit ? "var(--color-primary)" : "var(--color-border)", opacity: busLit ? 0.9 : 0.5 }}
        />
        {/* Down-stub + arrowhead into generation. */}
        <span
          className="absolute left-1/2 h-4 w-px -translate-x-1/2"
          style={{ top: "24px", backgroundColor: genColor, opacity: generationReached ? 0.9 : 0.5 }}
        />
        <ChevronDown
          size={14}
          className="absolute left-1/2 -translate-x-1/2"
          style={{ top: "34px", color: genColor, opacity: generationReached ? 1 : 0.5 }}
        />
      </div>
      {/* Mobile connector */}
      <div className="flex h-4 items-center justify-center sm:hidden">
        <span className="h-full w-px" style={{ backgroundColor: genColor, opacity: generationReached ? 0.9 : 0.5 }} />
      </div>
    </div>
  );
}

// A short vertical connector between stacked nodes. The moving dot only
// rides an active connector; motion is disabled via the global
// prefers-reduced-motion CSS override.
function Connector({ active }: { active: boolean }) {
  return (
    <div aria-hidden className="flex h-4 w-full items-center justify-center">
      <svg viewBox="0 0 8 16" width="8" height="16" className="overflow-visible">
        <line
          x1="4"
          y1="0"
          x2="4"
          y2="16"
          stroke={active ? "var(--color-primary)" : "var(--color-border)"}
          strokeWidth="2"
          strokeLinecap="round"
          strokeOpacity={active ? 0.9 : 0.5}
        />
        {active ? (
          <circle cx="4" cy="8" r="2" fill="var(--color-primary)" className="pipeline-dot" />
        ) : null}
      </svg>
    </div>
  );
}

function PipelineStatusBadge({
  state,
  isStreaming,
}: {
  state: PipelineState;
  isStreaming: boolean;
}) {
  if (state.cacheHit) {
    return <Badge variant="success">{state.cacheTier} cache hit</Badge>;
  }
  if (isStreaming) return <Badge variant="accent">live</Badge>;
  if (state.route === "REFUSE") return <Badge variant="critical">refused</Badge>;
  if (state.route) return <Badge variant="muted">{state.route.replace("_", " ").toLowerCase()}</Badge>;
  return <Badge variant="muted">idle</Badge>;
}
