"""Unit tests for the HybridRetriever orchestration.

Exercises the composition (BM25 + dense -> RRF -> rerank -> top-K) with fakes:
a canned BM25, a vector store whose matches carry losslessly-encoded chunk
metadata (so ``decode_chunk`` round-trips), and a fake reranker. No embedding or
reranker model is downloaded or loaded.
"""

from collections.abc import Sequence
from typing import Any

import pytest

from hybridrag.domain import RankedChunk
from hybridrag.indexing import VectorMatch, encode_chunk
from hybridrag.retrieval import HybridRetriever, Reranker
from hybridrag.retrieval.hybrid import RETRIEVER_NAME as DENSE_NAME
from hybridrag.retrieval.reranker import RETRIEVER_NAME as RERANK_NAME
from tests.unit.test_indexing import MODEL, FakeEmbeddings, _chunk


class FakeBM25:
    """A minimal stand-in for BM25Index returning canned RankedChunk lists."""

    def __init__(self, results: Sequence[RankedChunk]) -> None:
        self._results = list(results)
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, top_n: int | None = None) -> list[RankedChunk]:
        self.calls.append((query, top_n or 0))
        return list(self._results)


class FakeStore:
    """A VectorStore whose query returns matches built from encoded chunks."""

    def __init__(self, chunks: Sequence[Any]) -> None:
        self._records = [
            encode_chunk(c, embedding_model=MODEL, corpus_version="test-corpus-v1")
            for c in chunks
        ]
        self._texts = [c.text for c in chunks]
        self.calls: list[tuple[Sequence[float], int, dict[str, Any] | None]] = []

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        self.calls.append((embedding, top_k, where))
        return [
            VectorMatch(id=meta["chunk_id"], text=text, metadata=meta, distance=0.5 + i)
            for i, (meta, text) in enumerate(zip(self._records, self._texts))
        ][:top_k]


class FakeReranker:
    """A reranker that returns candidates unchanged (identity), tagged."""

    def __init__(self, model_name: str = "fake-reranker") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(self, query: str, candidates: Sequence[RankedChunk]) -> list[RankedChunk]:
        return [
            RankedChunk(
                chunk=c.chunk, score=float(1.0 / rank), rank=rank, retriever=RERANK_NAME
            )
            for rank, c in enumerate(candidates, start=1)
        ]


def _chunks(n: int) -> list[Any]:
    return [_chunk(i, f"text number {i} for chunk {chr(65 + i)}") for i in range(n)]


@pytest.fixture
def settings() -> Any:
    from hybridrag.config import Settings

    return Settings(
        bm25_top_n=10,
        dense_top_n=10,
        rerank_candidates=20,
        final_top_k=3,
    )


def _retriever(
    bm25_results: Sequence[RankedChunk],
    dense_chunks: Sequence[Any],
    *,
    reranker: Reranker | None = None,
    settings: Any | None = None,
) -> tuple[HybridRetriever, FakeBM25, FakeStore, FakeEmbeddings]:
    from hybridrag.config import Settings

    bm25 = FakeBM25(bm25_results)
    store = FakeStore(dense_chunks)
    embeddings = FakeEmbeddings()
    reranker = reranker or FakeReranker()
    return (
        HybridRetriever(bm25, store, embeddings, reranker, settings=settings or Settings()),
        bm25,
        store,
        embeddings,
    )


class TestHybridRetriever:
    def test_runs_both_retrievers_and_reranks(self, settings: Any) -> None:
        chunks = _chunks(4)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25")
            for i in range(4)
        ]
        retriever, bm25, store, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("what is remote work")
        assert bm25.calls and store.calls  # both retrievers were invoked
        assert out  # non-empty fused + reranked result
        # Final result is bounded by final_top_k and tagged with the reranker.
        assert len(out) <= settings.final_top_k
        assert all(r.retriever == RERANK_NAME for r in out)

    def test_preserves_chunk_id_and_authorization_metadata(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [
            RankedChunk(chunk=chunks[0], score=1.0, rank=1, retriever="bm25")
        ]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("what is remote work")
        assert [r.chunk_id for r in out]  # chunk_id preserved
        for r in out:
            assert r.chunk.allowed_roles == ("employee", "hr", "admin")
            assert r.chunk.document_id == "HR-003"

    def test_where_filter_is_forwarded_to_dense_retrieval(self, settings: Any) -> None:
        chunks = _chunks(2)
        retriever, _, store, _ = _retriever([], chunks, settings=settings)

        where = {"classification": "confidential"}
        retriever.retrieve("query", where=where)
        assert store.calls
        assert store.calls[0][2] == where

    def test_empty_dense_results_still_return_bm25_results(self, settings: Any) -> None:
        chunks = _chunks(2)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25")
            for i in range(2)
        ]
        retriever, _, _, _ = _retriever(bm25_results, [], settings=settings)

        out = retriever.retrieve("query")
        assert out
        assert all(r.chunk_id in {c.chunk_id for c in chunks} for r in out)

    def test_empty_bm25_results_still_return_dense_results(self, settings: Any) -> None:
        chunks = _chunks(2)
        retriever, _, _, _ = _retriever([], chunks, settings=settings)

        out = retriever.retrieve("query")
        assert out
        assert all(r.chunk_id in {c.chunk_id for c in chunks} for r in out)

    def test_final_top_k_bounds_the_result(self, settings: Any) -> None:
        chunks = _chunks(8)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25")
            for i in range(8)
        ]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("query")
        assert len(out) == settings.final_top_k

    def test_all_results_are_tagged_with_a_retriever(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25")
            for i in range(3)
        ]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("query")
        assert out
        assert all(r.retriever in {DENSE_NAME, "bm25", "rrf", RERANK_NAME} for r in out)
