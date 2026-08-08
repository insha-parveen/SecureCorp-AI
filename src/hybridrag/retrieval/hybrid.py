"""Hybrid retrieval orchestration: BM25 + dense -> RRF -> cross-encoder rerank.

This is the composition layer that ties the existing primitives together
(CLAUDE.md §7 "Hybrid search implementation"):

1. Run BM25 over the shared chunk corpus.
2. Run dense similarity search over the vector store.
3. Fuse both ranked lists with :func:`~hybridrag.retrieval.fusion.rrf_fuse`.
4. Rerank the bounded fused candidate set with
   :func:`~hybridrag.retrieval.reranker.rerank_top`.
5. Return the final top-K evidence chunks.

The orchestrator owns no retrieval logic of its own — it only wires the
existing ``BM25Index``, ``VectorStore``, ``EmbeddingProvider``, and ``Reranker``
abstractions together. Dense ``VectorMatch`` results are converted back to full
``Chunk`` objects via the lossless :func:`~hybridrag.indexing.chunk_metadata.decode_chunk`
codec, so every returned ``RankedChunk`` carries its authorization/provenance
metadata intact for the Phase 5 authorization layer.

An optional ``where`` filter is forwarded to dense retrieval only. Authorization
is intentionally NOT implemented here — that is a separate milestone.
"""

from collections.abc import Sequence
from typing import Any

from hybridrag.config import Settings, get_settings
from hybridrag.domain import RankedChunk
from hybridrag.indexing import (
    BM25Index,
    EmbeddingProvider,
    VectorStore,
    decode_chunk,
)
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.reranker import Reranker, rerank_top

RETRIEVER_NAME = "dense"


class HybridRetriever:
    """Compose BM25 + dense retrieval, RRF fusion, and cross-encoder reranking."""

    def __init__(
        self,
        bm25: BM25Index,
        store: VectorStore,
        embeddings: EmbeddingProvider,
        reranker: Reranker,
        *,
        settings: Settings | None = None,
    ) -> None:
        self._bm25 = bm25
        self._store = store
        self._embeddings = embeddings
        self._reranker = reranker
        self._settings = settings or get_settings()

    def retrieve(
        self, query: str, *, where: dict[str, Any] | None = None
    ) -> list[RankedChunk]:
        """Return the final top-K evidence chunks for ``query``.

        Args:
            query: The user's natural-language question.
            where: Optional metadata filter forwarded to dense retrieval only
                (the hook the Phase 5 authorization layer will use). BM25 has no
                equivalent filter, so it is not applied there.

        Returns:
            The reranked ``final_top_k`` ``RankedChunk`` results, best first.
        """
        cfg = self._settings

        bm25_results = self._bm25.search(query, top_n=cfg.bm25_top_n)
        dense_results = self._dense_search(query, where=where, top_n=cfg.dense_top_n)

        fused = rrf_fuse(bm25_results, dense_results)
        return rerank_top(
            query,
            fused,
            reranker=self._reranker,
            rerank_candidates=cfg.rerank_candidates,
            final_top_k=cfg.final_top_k,
        )

    # -- internals ---------------------------------------------------------

    def _dense_search(
        self, query: str, *, where: dict[str, Any] | None, top_n: int
    ) -> list[RankedChunk]:
        """Run dense similarity search and convert matches to ``RankedChunk``."""
        embedding = self._embeddings.embed_query(query)
        matches = self._store.query(embedding, top_k=top_n, where=where)
        return [
            RankedChunk(
                chunk=decode_chunk(match.text, match.metadata),
                score=float(match.distance),
                rank=rank,
                retriever=RETRIEVER_NAME,
            )
            for rank, match in enumerate(matches, start=1)
        ]
