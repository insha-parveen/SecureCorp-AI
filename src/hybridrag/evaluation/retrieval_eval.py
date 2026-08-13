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

Accepts either a JSON list (legacy) or a JSONL file (Phase 8 golden set).
"""

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings
from hybridrag.domain import RankedChunk
from hybridrag.indexing import (
    BM25Index,
    ChromaVectorStore,
    get_embedding_provider,
)
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker

# Admin user for the eval harness so the golden set is not gated by role
# checks. The harness measures retrieval quality, not authorization.
_EVAL_USER_CONTEXT = UserContext(
    user_id="eval", roles=("admin",), department="HR", tenant_id="nexacore"
)


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


class RetrievalEvaluator:
    """Evaluates a retrieval pipeline against a golden set of queries."""

    def __init__(
        self,
        queries_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._queries = _load_queries(queries_path)
        # Pre-extract categories for per-category breakdown
        self._has_categories = any("category" in q for q in self._queries)

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

            results = retrieval_fn(query_text, _EVAL_USER_CONTEXT)

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
    evaluator = RetrievalEvaluator(queries_path, settings=cfg)

    # Initialize components once
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    embeddings = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)

    # Warm up models: Force a load now so we catch network errors early
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])

    hybrid = HybridRetriever(bm25, store, embeddings, reranker, settings=cfg)

    # Define the 4 arms
    # We use the retrieved chunk_id to resolve the full Chunk object from BM25's
    # in-memory store, which is the most efficient way to get the full metadata.
    arms: list[tuple[str, Callable[[str, UserContext], list[RankedChunk]]]] = [
        (
            "Dense-Only",
            lambda q, _user: [
                RankedChunk(chunk=chunk, score=res.distance, rank=r, retriever="dense")
                for r, res in enumerate(
                    store.query(embeddings.embed_query(q), top_k=cfg.dense_top_n), start=1
                )
                if (chunk := bm25.get(res.id)) is not None
            ],
        ),
        ("BM25-Only", lambda q, user: bm25.search(q, user_context=user, top_n=cfg.bm25_top_n)),
        (
            "Hybrid-RRF",
            lambda q, user: rrf_fuse(
                bm25.search(q, user_context=user, top_n=cfg.bm25_top_n),
                [
                    RankedChunk(chunk=chunk, score=res.distance, rank=r, retriever="dense")
                    for r, res in enumerate(
                        store.query(embeddings.embed_query(q), top_k=cfg.dense_top_n), start=1
                    )
                    if (chunk := bm25.get(res.id)) is not None
                ],
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
    evaluator = RetrievalEvaluator(queries_path, settings=cfg)

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
        bm25 = hybrid._bm25
        if not isinstance(hybrid._store, ChromaVectorStore):
            raise TypeError(
                f"HybridRetriever._store must be ChromaVectorStore for ablation arms; "
                f"got {type(hybrid._store).__name__}"
            )
        store = hybrid._store
        embeddings = hybrid._embeddings

    arms: list[tuple[str, Callable[[str, UserContext], list[RankedChunk]]]] = [
        (
            "Dense-Only",
            lambda q, _user: [
                RankedChunk(chunk=chunk, score=res.distance, rank=r, retriever="dense")
                for r, res in enumerate(
                    store.query(embeddings.embed_query(q), top_k=cfg.dense_top_n), start=1
                )
                if (chunk := bm25.get(res.id)) is not None
            ],
        ),
        ("BM25-Only", lambda q, user: bm25.search(q, user_context=user, top_n=cfg.bm25_top_n)),
        (
            "Hybrid-RRF",
            lambda q, user: rrf_fuse(
                bm25.search(q, user_context=user, top_n=cfg.bm25_top_n),
                [
                    RankedChunk(chunk=chunk, score=res.distance, rank=r, retriever="dense")
                    for r, res in enumerate(
                        store.query(embeddings.embed_query(q), top_k=cfg.dense_top_n), start=1
                    )
                    if (chunk := bm25.get(res.id)) is not None
                ],
            ),
        ),
        ("Hybrid-Rerank", lambda q, user: hybrid.retrieve(q, user_context=user)),
    ]

    results = []
    for name, fn in arms:
        results.append(evaluator.evaluate_detailed(fn, name))
    return results
