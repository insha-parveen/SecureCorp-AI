"""Retrieval evaluation harness for the HybridRAG pipeline.

This module implements a deterministic ablation study to measure the impact of
different retrieval strategies (Dense, BM25, Hybrid RRF, Hybrid Rerank) on
retrieval quality across the golden dataset.

Metrics measured (per CLAUDE.md §13):
- Recall@K: proportion of queries with at least one expected document retrieved within top-K.
- MRR (Mean Reciprocal Rank): 1 / rank of the first correct document, averaged.
- nDCG@K: normalized Discounted Cumulative Gain at K.
- Precision@K: proportion of top-K results that are relevant.
- Hit@1: proportion of queries where the first result is correct.

Plus per-category breakdown (every CLAUDE.md §14 category gets its own
Recall@K, MRR, nDCG@K, Precision@K).

All four arms enforce authorization for a single fixed eval user, so the table
is apples-to-apples and reflects the production auth-enforced path. See
``_authorized_dense`` and the ``_EVAL_USER_CONTEXT`` note for why this shared
authorization ceiling keeps the arm-vs-arm comparison fair.

Accepts either a JSON list (legacy) or a JSONL file (Phase 8 golden set).
"""

import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hybridrag.authorization.engine import AuthorizationEngine
from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings
from hybridrag.domain import Chunk, RankedChunk
from hybridrag.indexing import (
    BM25Index,
    ChromaVectorStore,
    EmbeddingProvider,
    get_embedding_provider,
)
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker

_EVAL_TENANT = "nexacore"

# Fallback identity, used for rows with no expected documents (refuse/abstain)
# and by callers that do not supply a resolver. ALL FOUR arms enforce
# authorization uniformly — BM25 filters inside ``.search``, dense via
# ``_authorized_dense`` below, and Hybrid-Rerank via ``hybrid.retrieve`` — so
# the arms stay directly comparable and reflect the production auth-enforced
# path. This user is ``admin``/HR and gets NO superuser bypass, so on its own it
# imposes a recall ceiling: golden documents requiring another department are
# legitimately unseen. ``build_authorized_user_resolver`` removes that ceiling
# per query without weakening the authorization check itself.
_EVAL_USER_CONTEXT = UserContext(
    user_id="eval", roles=("admin",), department="HR", tenant_id=_EVAL_TENANT
)


def _authorized_dense(
    query: str,
    *,
    store: ChromaVectorStore,
    embeddings: EmbeddingProvider,
    bm25: BM25Index,
    user_context: UserContext,
    settings: Settings,
) -> list[RankedChunk]:
    """Dense retrieval with the SAME authorization the production path applies.

    Mirrors :meth:`HybridRetriever._dense_search`: NO authorization ``where``
    clause is pushed to Chroma (the narrow pre-filter dropped
    authorized-but-role-gated docs from the candidate pool); instead every match
    is post-filtered through
    :meth:`~hybridrag.authorization.engine.AuthorizationEngine.is_authorized`,
    which is the actual security boundary. Chunk objects are resolved from the
    in-memory BM25 store by ``chunk_id``. Keeping this in lockstep with
    ``_dense_search`` is what makes the Dense-Only / Hybrid-RRF arms reflect the
    real production path rather than an idealized auth-off one.
    """
    matches = store.query(embeddings.embed_query(query), top_k=settings.dense_top_n)
    ranked: list[RankedChunk] = []
    for rank, match in enumerate(matches, start=1):
        chunk = bm25.get(match.id)
        if chunk is None or not AuthorizationEngine.is_authorized(user_context, chunk):
            continue
        ranked.append(
            RankedChunk(chunk=chunk, score=float(match.distance), rank=rank, retriever="dense")
        )
    return ranked


@dataclass(frozen=True)
class RetrievalMetric:
    strategy: str
    recall_at_k: float
    mrr: float
    hits: int
    total: int
    # Phase 8 extensions
    ndcg_at_k: float = 0.0
    precision_at_k: float = 0.0
    hit_at_1: float = 0.0


@dataclass(frozen=True)
class PerCategoryMetrics:
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    precision_at_k: float
    hits: int
    total: int


@dataclass(frozen=True)
class DetailedRetrievalResult:
    """A RetrievalMetric enriched with per-category breakdown and config."""

    strategy: str
    overall: RetrievalMetric
    by_category: dict[str, PerCategoryMetrics] = field(default_factory=dict)


def _load_queries(path: Path) -> list[dict[str, Any]]:
    """Load queries from either a JSON list or a JSONL file (auto-detected)."""
    with path.open(encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            result: list[dict[str, Any]] = json.load(f)
            return result
        out: list[dict[str, Any]] = []
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out


def _ndcg_at_k(expected: set[str], retrieved: list[RankedChunk], k: int) -> float:
    """nDCG@K with binary relevance (1 if doc_id ∈ expected, else 0)."""
    if not expected or k <= 0:
        return 0.0
    dcg = 0.0
    for i, res in enumerate(retrieved[:k], start=1):
        rel = 1.0 if res.chunk.document_id in expected else 0.0
        dcg += rel / math.log2(i + 1)
    # Ideal DCG: all expected docs at the top (up to k).
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(expected), k) + 1))
    if ideal == 0.0:
        return 0.0
    return dcg / ideal


def _precision_at_k(expected: set[str], retrieved: list[RankedChunk], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r.chunk.document_id in expected)
    return hits / len(top_k)


def _expected_docs(row: dict[str, Any]) -> list[str]:
    """The golden row's expected document ids, minus wildcards/blanks."""
    raw = row.get("expected_chunk_sources") or row.get("expected_documents") or []
    return [d for d in raw if d and d != "*"]


def build_authorized_user_resolver(
    chunks: Sequence[Chunk],
) -> Callable[[dict[str, Any]], UserContext]:
    """Build a per-query identity that is authorized for that query's answer.

    WHY: with one fixed eval identity, every golden document that identity may
    not read counts as a retrieval miss — so the score conflates "retrieval
    failed" with "authorization correctly refused". On this corpus that put a
    hard ceiling of roughly 10 points on every arm.

    This does NOT weaken authorization. ``is_authorized`` still runs on every
    retrieved chunk, and chunks outside the resolved identity's scope are still
    excluded; we only stop penalizing retrieval for documents the *arbitrary*
    eval user happened to lack. The resolved identity is derived from the golden
    row itself: its ``expected_roles`` plus the roles/departments the expected
    documents actually grant. A user has exactly one department, so when a
    query's expected documents span departments we pick the department that
    authorizes the most of them — see ``residual_auth_ceiling`` for how many
    rows remain partially unreachable.

    Rows with no expected documents (refuse/abstain cases) fall back to the
    fixed identity, since there is nothing to be authorized for.
    """
    by_doc: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk.document_id, []).append(chunk)

    def resolve(row: dict[str, Any]) -> UserContext:
        expected = _expected_docs(row)
        if not expected:
            return _EVAL_USER_CONTEXT

        roles: set[str] = set(row.get("expected_roles") or ())
        departments: set[str] = set()
        for doc_id in expected:
            for chunk in by_doc.get(doc_id, ()):
                roles.update(chunk.allowed_roles)
                if chunk.department:
                    departments.add(chunk.department)
                departments.update(chunk.allowed_departments)

        def candidate(department: str | None) -> UserContext:
            return UserContext(
                user_id="eval",
                roles=tuple(sorted(roles)),
                department=department,
                tenant_id=_EVAL_TENANT,
            )

        # One department per user, so choose the one covering the most expected
        # documents. Deterministic: ties break on the sorted department name.
        # An empty set still needs one attempt with department=None (a
        # public/role-only document needs no department match).
        candidates: list[str | None] = list(sorted(departments)) if departments else [None]
        best = _EVAL_USER_CONTEXT
        best_covered = -1
        for department in candidates:
            user = candidate(department)
            covered = sum(
                1
                for doc_id in expected
                if any(
                    AuthorizationEngine.is_authorized(user, chunk)
                    for chunk in by_doc.get(doc_id, ())
                )
            )
            if covered > best_covered:
                best, best_covered = user, covered
        return best

    return resolve


def residual_auth_ceiling(
    queries: Sequence[dict[str, Any]],
    chunks: Sequence[Chunk],
) -> dict[str, int]:
    """Count golden rows the per-query identity still cannot fully reach.

    Reported alongside the metrics so the remaining ceiling is visible rather
    than silently depressing the score. ``fully_reachable`` rows have every
    expected document authorized; ``partial`` and ``unreachable`` rows cap the
    best achievable recall no matter how good retrieval is.
    """
    resolve = build_authorized_user_resolver(chunks)
    by_doc: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk.document_id, []).append(chunk)

    counts = {"fully_reachable": 0, "partial": 0, "unreachable": 0, "no_expected_docs": 0}
    for row in queries:
        expected = _expected_docs(row)
        if not expected:
            counts["no_expected_docs"] += 1
            continue
        user = resolve(row)
        covered = sum(
            1
            for doc_id in expected
            if any(
                AuthorizationEngine.is_authorized(user, chunk) for chunk in by_doc.get(doc_id, ())
            )
        )
        if covered == len(expected):
            counts["fully_reachable"] += 1
        elif covered:
            counts["partial"] += 1
        else:
            counts["unreachable"] += 1
    return counts


class RetrievalEvaluator:
    """Evaluates a retrieval pipeline against a golden set of queries."""

    def __init__(
        self,
        queries_path: Path,
        settings: Settings | None = None,
        user_context_for: Callable[[dict[str, Any]], UserContext] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._queries = _load_queries(queries_path)
        # Pre-extract categories for per-category breakdown
        self._has_categories = any("category" in q for q in self._queries)
        # Per-row identity resolver. Defaults to the single fixed eval user,
        # which imposes an authorization ceiling on the score — see
        # ``build_authorized_user_resolver``.
        self._user_context_for = user_context_for or (lambda _row: _EVAL_USER_CONTEXT)

    def _evaluate_arm(
        self,
        retrieval_fn: Callable[[str, UserContext], list[RankedChunk]],
        strategy_name: str,
        k: int = 5,
    ) -> DetailedRetrievalResult:
        # Aggregators — overall
        hits = 0
        sum_rr = 0.0
        sum_ndcg = 0.0
        sum_prec = 0.0
        hit_at_1 = 0
        total = len(self._queries)

        # Aggregators — per category
        cat_hits: dict[str, int] = {}
        cat_sum_rr: dict[str, float] = {}
        cat_sum_ndcg: dict[str, float] = {}
        cat_sum_prec: dict[str, float] = {}
        cat_hit_at_1: dict[str, int] = {}
        cat_total: dict[str, int] = {}

        for q in self._queries:
            query_text = q["query"]
            expected_docs = set(q.get("expected_chunk_sources", q.get("expected_documents", [])))
            category = q.get("category", "_uncategorized")

            results = retrieval_fn(query_text, self._user_context_for(q))

            # Per-query metrics
            first_hit_rank = 0
            for rank, res in enumerate(results, start=1):
                if res.chunk.document_id in expected_docs:
                    first_hit_rank = rank
                    break

            is_hit_within_k = first_hit_rank > 0 and first_hit_rank <= k
            is_hit_at_1 = first_hit_rank == 1

            if is_hit_within_k:
                hits += 1
            if first_hit_rank > 0:
                sum_rr += 1.0 / first_hit_rank
            if is_hit_at_1:
                hit_at_1 += 1

            ndcg = _ndcg_at_k(expected_docs, results, k)
            prec = _precision_at_k(expected_docs, results, k)
            sum_ndcg += ndcg
            sum_prec += prec

            # Per-category accumulators
            cat_total[category] = cat_total.get(category, 0) + 1
            if is_hit_within_k:
                cat_hits[category] = cat_hits.get(category, 0) + 1
            if first_hit_rank > 0:
                cat_sum_rr[category] = cat_sum_rr.get(category, 0.0) + 1.0 / first_hit_rank
            if is_hit_at_1:
                cat_hit_at_1[category] = cat_hit_at_1.get(category, 0) + 1
            cat_sum_ndcg[category] = cat_sum_ndcg.get(category, 0.0) + ndcg
            cat_sum_prec[category] = cat_sum_prec.get(category, 0.0) + prec

        overall = RetrievalMetric(
            strategy=strategy_name,
            recall_at_k=hits / total if total > 0 else 0,
            mrr=sum_rr / total if total > 0 else 0,
            hits=hits,
            total=total,
            ndcg_at_k=sum_ndcg / total if total > 0 else 0,
            precision_at_k=sum_prec / total if total > 0 else 0,
            hit_at_1=hit_at_1 / total if total > 0 else 0,
        )

        by_category: dict[str, PerCategoryMetrics] = {}
        for cat, n in cat_total.items():
            by_category[cat] = PerCategoryMetrics(
                recall_at_k=cat_hits.get(cat, 0) / n if n > 0 else 0,
                mrr=cat_sum_rr.get(cat, 0.0) / n if n > 0 else 0,
                ndcg_at_k=cat_sum_ndcg.get(cat, 0.0) / n if n > 0 else 0,
                precision_at_k=cat_sum_prec.get(cat, 0.0) / n if n > 0 else 0,
                hits=cat_hits.get(cat, 0),
                total=n,
            )

        return DetailedRetrievalResult(
            strategy=strategy_name,
            overall=overall,
            by_category=by_category,
        )

    def evaluate(
        self,
        retrieval_fn: Callable[[str, UserContext], list[RankedChunk]],
        strategy_name: str,
        k: int = 5,
    ) -> RetrievalMetric:
        """Backward-compatible evaluate() returning just the overall metric."""
        return self._evaluate_arm(retrieval_fn, strategy_name, k).overall

    def evaluate_detailed(
        self,
        retrieval_fn: Callable[[str, UserContext], list[RankedChunk]],
        strategy_name: str,
        k: int = 5,
    ) -> DetailedRetrievalResult:
        """Returns overall metric + per-category breakdown."""
        return self._evaluate_arm(retrieval_fn, strategy_name, k)


def run_ablation_study(
    queries_path: Path,
    settings: Settings | None = None,
) -> list[RetrievalMetric]:
    """Compare the four main retrieval arms of the HybridRAG architecture.

    Pre-loads models to avoid redundant network checks and ensure stability.
    Returns the 4 overall metrics as a flat list (backward compatible).
    """
    cfg = settings or get_settings()

    # Initialize components once
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    embeddings = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)

    # Per-query authorized identity, so the score measures retrieval rather
    # than the arbitrary eval user's clearance (see the resolver's docstring).
    evaluator = RetrievalEvaluator(
        queries_path,
        settings=cfg,
        user_context_for=build_authorized_user_resolver(bm25.chunks),
    )

    # Warm up models: Force a load now so we catch network errors early
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])

    hybrid = HybridRetriever(bm25, store, embeddings, reranker, settings=cfg)

    # Define the 4 arms. Every arm enforces authorization for the eval user so
    # the table is apples-to-apples: BM25 filters inside ``.search``, the dense
    # arms go through ``_authorized_dense`` (auth ``where`` + is_authorized
    # post-filter), and Hybrid-Rerank uses the production ``hybrid.retrieve``.
    def _dense(q: str, user: UserContext) -> list[RankedChunk]:
        return _authorized_dense(
            q, store=store, embeddings=embeddings, bm25=bm25, user_context=user, settings=cfg
        )

    arms: list[tuple[str, Callable[[str, UserContext], list[RankedChunk]]]] = [
        ("Dense-Only", _dense),
        ("BM25-Only", lambda q, user: bm25.search(q, user_context=user, top_n=cfg.bm25_top_n)),
        (
            "Hybrid-RRF",
            lambda q, user: rrf_fuse(
                bm25.search(q, user_context=user, top_n=cfg.bm25_top_n), _dense(q, user)
            ),
        ),
        ("Hybrid-Rerank", lambda q, user: hybrid.retrieve(q, user_context=user)),
    ]

    results = []
    for name, fn in arms:
        results.append(evaluator.evaluate(fn, name))

    return results


def run_ablation_study_detailed(
    queries_path: Path,
    settings: Settings | None = None,
    prebuilt: HybridRetriever | None = None,
) -> list[DetailedRetrievalResult]:
    """Same as ``run_ablation_study`` but returns per-category breakdown.

    If ``prebuilt`` is supplied (a pre-warmed HybridRetriever), the harness
    reuses it instead of building its own — used by the chunking sweep to
    share model loads across grid cells.
    """
    cfg = settings or get_settings()

    if prebuilt is None:
        bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
        store = ChromaVectorStore.from_settings(cfg)
        embeddings = get_embedding_provider(cfg)
        reranker = CrossEncoderReranker.from_settings(cfg)
        # Warm up so a missing model fails fast, not silently mid-sweep
        embeddings.embed_query("warmup")
        reranker.rerank("warmup", [])
        hybrid = HybridRetriever(bm25, store, embeddings, reranker, settings=cfg)
    else:
        hybrid = prebuilt
        bm25 = hybrid.bm25
        if not isinstance(hybrid._store, ChromaVectorStore):
            raise TypeError(
                f"HybridRetriever._store must be ChromaVectorStore for ablation arms; "
                f"got {type(hybrid._store).__name__}"
            )
        store = hybrid._store
        embeddings = hybrid._embeddings

    # Per-query authorized identity, so the score measures retrieval rather
    # than the arbitrary eval user's clearance (see the resolver's docstring).
    evaluator = RetrievalEvaluator(
        queries_path,
        settings=cfg,
        user_context_for=build_authorized_user_resolver(bm25.chunks),
    )

    def _dense(q: str, user: UserContext) -> list[RankedChunk]:
        return _authorized_dense(
            q, store=store, embeddings=embeddings, bm25=bm25, user_context=user, settings=cfg
        )

    arms: list[tuple[str, Callable[[str, UserContext], list[RankedChunk]]]] = [
        ("Dense-Only", _dense),
        ("BM25-Only", lambda q, user: bm25.search(q, user_context=user, top_n=cfg.bm25_top_n)),
        (
            "Hybrid-RRF",
            lambda q, user: rrf_fuse(
                bm25.search(q, user_context=user, top_n=cfg.bm25_top_n), _dense(q, user)
            ),
        ),
        ("Hybrid-Rerank", lambda q, user: hybrid.retrieve(q, user_context=user)),
    ]

    results = []
    for name, fn in arms:
        results.append(evaluator.evaluate_detailed(fn, name))
    return results
