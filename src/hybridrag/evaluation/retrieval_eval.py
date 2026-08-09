"""Retrieval evaluation harness for the HybridRAG pipeline.

This module implements a deterministic ablation study to measure the impact of
different retrieval strategies (Dense, BM25, Hybrid RRF, Hybrid Rerank) on
retrieval quality across the golden dataset.

Metrics measured:
- Recall@K: Proportion of queries where at least one expected document is retrieved.
- MRR (Mean Reciprocal Rank): The average of 1 / rank of the first correct document.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

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


class RetrievalEvaluator:
    """Evaluates a retrieval pipeline against a golden set of queries."""

    def __init__(
        self,
        queries_path: Path,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        with open(queries_path, encoding="utf-8") as f:
            self._queries = json.load(f)

    def evaluate(
        self,
        retrieval_fn: Callable[[str, UserContext], list[RankedChunk]],
        strategy_name: str,
        k: int = 5,
    ) -> RetrievalMetric:
        """Run a retrieval function across all golden queries and calculate metrics."""
        hits = 0
        sum_rr = 0.0
        total = len(self._queries)

        for q in self._queries:
            query_text = q["query"]
            expected_docs = set(q.get("expected_chunk_sources", q.get("expected_documents", [])))

            # Anonymous, unrestricted user — the eval harness must surface
            # every relevant chunk regardless of authorization scope.
            results = retrieval_fn(query_text, _EVAL_USER_CONTEXT)

            # Find the rank of the first correct document
            first_hit_rank = 0
            for rank, res in enumerate(results, start=1):
                if res.chunk.document_id in expected_docs:
                    first_hit_rank = rank
                    break

            if first_hit_rank > 0 and first_hit_rank <= k:
                hits += 1
                sum_rr += 1.0 / first_hit_rank
            elif first_hit_rank > k:
                # Still a hit, but outside our top-K window for Recall
                # MRR is usually calculated over the full list or a large window
                sum_rr += 1.0 / first_hit_rank

        return RetrievalMetric(
            strategy=strategy_name,
            recall_at_k=hits / total if total > 0 else 0,
            mrr=sum_rr / total if total > 0 else 0,
            hits=hits,
            total=total,
        )


def run_ablation_study(
    queries_path: Path,
    settings: Settings | None = None,
) -> list[RetrievalMetric]:
    """Compare the four main retrieval arms of the HybridRAG architecture.

    Pre-loads models to avoid redundant network checks and ensure stability.
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
