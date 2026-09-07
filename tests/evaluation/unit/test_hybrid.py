"""Unit tests for the HybridRetriever orchestration.

Exercises the composition (BM25 + dense -> RRF -> rerank -> top-K) with fakes:
a canned BM25, a vector store whose matches carry losslessly-encoded chunk
metadata (so ``decode_chunk`` round-trips), and a fake reranker. No embedding or
reranker model is downloaded or loaded.
"""

from collections.abc import Sequence
from typing import Any

import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.domain import RankedChunk
from hybridrag.indexing import VectorMatch, encode_chunk
from hybridrag.retrieval import HybridRetriever, Reranker
from hybridrag.retrieval.hybrid import RETRIEVER_NAME as DENSE_NAME
from hybridrag.retrieval.reranker import RETRIEVER_NAME as RERANK_NAME
from tests.evaluation.unit.test_indexing import MODEL, FakeEmbeddings, _chunk

# Dummy user that satisfies the basic authorization checks performed by the
# retriever's dense filter (employee + HR department).
DUMMY_USER = UserContext(user_id="test_user", roles=("employee", "hr", "admin"), department="HR")


class FakeBM25:
    """A minimal stand-in for BM25Index returning canned RankedChunk lists."""

    def __init__(self, results: Sequence[RankedChunk]) -> None:
        self._results = list(results)
        self.calls: list[tuple[str, int]] = []

    def search(
        self,
        query: str,
        user_context: UserContext | None = None,
        top_n: int | None = None,
    ) -> list[RankedChunk]:
        self.calls.append((query, top_n or 0))
        return list(self._results)


class FakeStore:
    """A VectorStore whose query returns matches built from encoded chunks."""

    def __init__(self, chunks: Sequence[Any]) -> None:
        self._records = [
            encode_chunk(c, embedding_model=MODEL, corpus_version="test-corpus-v1") for c in chunks
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
            for i, (meta, text) in enumerate(zip(self._records, self._texts, strict=False))
        ][:top_k]


class FakeReranker:
    """A reranker that returns candidates unchanged (identity), tagged.

    Records every call so tests can assert whether it ran at all.
    """

    def __init__(self, model_name: str = "fake-reranker") -> None:
        self._model_name = model_name
        self.calls: list[str] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(self, query: str, candidates: Sequence[RankedChunk]) -> list[RankedChunk]:
        self.calls.append(query)
        return [
            RankedChunk(chunk=c.chunk, score=float(1.0 / rank), rank=rank, retriever=RERANK_NAME)
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
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(4)
        ]
        retriever, bm25, store, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("what is remote work", user_context=DUMMY_USER)
        assert bm25.calls and store.calls  # both retrievers were invoked
        assert out  # non-empty fused + reranked result
        # Final result is bounded by final_top_k and tagged with the reranker.
        assert len(out) <= settings.final_top_k
        assert all(r.retriever == RERANK_NAME for r in out)

    def test_preserves_chunk_id_and_authorization_metadata(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [RankedChunk(chunk=chunks[0], score=1.0, rank=1, retriever="bm25")]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("what is remote work", user_context=DUMMY_USER)
        assert [r.chunk_id for r in out]  # chunk_id preserved
        for r in out:
            assert r.chunk.allowed_roles == ("employee", "hr", "admin")
            assert r.chunk.document_id == "HR-003"

    def test_where_filter_is_forwarded_to_dense_retrieval(self, settings: Any) -> None:
        chunks = _chunks(2)
        retriever, _, store, _ = _retriever([], chunks, settings=settings)

        where = {"classification": "confidential"}
        retriever.retrieve("query", user_context=DUMMY_USER, where=where)
        assert store.calls
        # The caller-supplied filter is forwarded directly — there is no longer
        # an auth pre-filter merged in, because auth is enforced by the
        # is_authorized post-filter instead (see hybrid.py).
        forwarded = store.calls[0][2]
        assert forwarded == where

    def test_empty_dense_results_still_return_bm25_results(self, settings: Any) -> None:
        chunks = _chunks(2)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(2)
        ]
        retriever, _, _, _ = _retriever(bm25_results, [], settings=settings)

        out = retriever.retrieve("query", user_context=DUMMY_USER)
        assert out
        assert all(r.chunk_id in {c.chunk_id for c in chunks} for r in out)

    def test_empty_bm25_results_still_return_dense_results(self, settings: Any) -> None:
        chunks = _chunks(2)
        retriever, _, _, _ = _retriever([], chunks, settings=settings)

        out = retriever.retrieve("query", user_context=DUMMY_USER)
        assert out
        assert all(r.chunk_id in {c.chunk_id for c in chunks} for r in out)

    def test_final_top_k_bounds_the_result(self, settings: Any) -> None:
        chunks = _chunks(8)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(8)
        ]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("query", user_context=DUMMY_USER)
        assert len(out) == settings.final_top_k

    def test_all_results_are_tagged_with_a_retriever(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(3)
        ]
        retriever, _, _, _ = _retriever(bm25_results, chunks, settings=settings)

        out = retriever.retrieve("query", user_context=DUMMY_USER)
        assert out
        assert all(r.retriever in {DENSE_NAME, "bm25", "rrf", RERANK_NAME} for r in out)

    def test_unauthorized_dense_chunk_never_reaches_output(self, settings: Any) -> None:
        """Security boundary: with no Chroma auth pre-filter, the is_authorized
        POST-filter must still exclude a chunk the store returns but the user
        cannot see. This guards the #1 change (dropping the narrow pre-filter):
        recall went up, but "zero unauthorized chunks reach the LLM" must hold.
        """
        from hybridrag.domain import Classification

        # A CONFIDENTIAL Finance chunk: the HR/employee/hr/admin DUMMY_USER is
        # NOT authorized for it (confidential needs role AND department match,
        # and the user's department is HR, not Finance).
        forbidden = _chunk(
            0,
            "confidential finance salary data",
            document_id="FIN-001",
            chunk_id="FIN-001:v1:0000",
            department="Finance",
            classification=Classification.CONFIDENTIAL,
            allowed_roles=("finance",),
            allowed_departments=("Finance",),
        )
        allowed = _chunk(1, "public remote work note", classification=Classification.PUBLIC)

        # The store returns BOTH; BM25 returns nothing. Only ``allowed`` may
        # survive. FakeStore ignores ``where`` anyway, which is exactly the
        # threat model: the post-filter — not the query filter — is the boundary.
        retriever, _, _, _ = _retriever([], [forbidden, allowed], settings=settings)

        out = retriever.retrieve("salary", user_context=DUMMY_USER)
        returned_docs = {r.chunk.document_id for r in out}
        assert "FIN-001" not in returned_docs, "unauthorized confidential chunk leaked to output"
        assert returned_docs == {"HR-003"}


class TestIdentifierRerankBypass:
    """The cross-encoder must not run on exact-identifier lookups.

    On an ID query the reranker scores semantic prose above the chunk that
    literally contains the identifier, which measured as exact_identifier
    Recall@5 dropping 100% -> 0% on the holdout. BM25 already ranks those
    correctly, so the fused order is kept and the ~1s rerank pass is skipped.
    """

    def test_identifier_query_skips_the_reranker(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(3)
        ]
        reranker = FakeReranker()
        retriever, _, _, _ = _retriever(bm25_results, chunks, reranker=reranker, settings=settings)

        out = retriever.retrieve("What does ITSEC-002 require?", user_context=DUMMY_USER)

        assert reranker.calls == [], "reranker ran on an exact-identifier query"
        # Results still come back — the fused order is returned, bounded by K.
        assert out
        assert len(out) <= settings.final_top_k
        assert all(r.retriever != RERANK_NAME for r in out)

    def test_semantic_query_still_reranks(self, settings: Any) -> None:
        chunks = _chunks(3)
        bm25_results = [
            RankedChunk(chunk=chunks[i], score=1.0, rank=i + 1, retriever="bm25") for i in range(3)
        ]
        reranker = FakeReranker()
        retriever, _, _, _ = _retriever(bm25_results, chunks, reranker=reranker, settings=settings)

        out = retriever.retrieve("what is the remote work policy", user_context=DUMMY_USER)

        assert reranker.calls, "reranker was skipped on a non-identifier query"
        assert all(r.retriever == RERANK_NAME for r in out)

    def test_bypass_can_be_disabled_by_config(self) -> None:
        from hybridrag.config import Settings

        cfg = Settings(
            bm25_top_n=10,
            dense_top_n=10,
            rerank_candidates=20,
            final_top_k=3,
            rerank_skip_identifier_queries=False,
        )
        chunks = _chunks(2)
        reranker = FakeReranker()
        retriever, _, _, _ = _retriever([], chunks, reranker=reranker, settings=cfg)

        retriever.retrieve("What does ITSEC-002 require?", user_context=DUMMY_USER)
        assert reranker.calls, "config flag did not re-enable reranking"
