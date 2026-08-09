"""Unit tests for RRF fusion and cross-encoder reranking.

Everything here runs against synthetic chunks and a fake reranker — no model is
downloaded or loaded. ``CrossEncoderReranker`` imports sentence-transformers
lazily, so constructing it never touches torch; we exercise the protocol and the
bounding/trimming helper ``rerank_top`` only.
"""

from collections.abc import Sequence
from datetime import date

from hybridrag.domain import (
    Chunk,
    Classification,
    RankedChunk,
    SourceType,
    content_hash,
)
from hybridrag.retrieval import Reranker, rerank_top, rrf_fuse
from hybridrag.retrieval.fusion import RETRIEVER_NAME as RRF_NAME
from hybridrag.retrieval.reranker import RETRIEVER_NAME as RERANK_NAME


def _results(ids: list[str], retriever: str) -> list[RankedChunk]:
    """Build RankedChunk lists with chunk_id = the supplied id string."""
    return [
        RankedChunk(
            chunk=_chunk_named(chunk_id, i, f"text for {chunk_id}"),
            score=float(len(ids) - i),
            rank=rank,
            retriever=retriever,
        )
        for rank, (i, chunk_id) in enumerate(enumerate(ids), start=1)
    ]


def _chunk_named(chunk_id: str, index: int, text: str) -> Chunk:
    """A Chunk whose ``chunk_id`` is an explicit string (not derived from index)."""
    return Chunk(
        chunk_id=chunk_id,
        document_id=chunk_id.split(":")[0],
        document_version="v1",
        text=text,
        chunk_index=index,
        token_count=len(text.split()),
        content_hash=content_hash(text),
        source_type=SourceType.POLICY,
        document_type="policy",
        department="HR",
        classification=Classification.PUBLIC,
        allowed_roles=("employee",),
        effective_date=date(2025, 1, 1),
    )


class TestRRFFusion:
    def test_present_in_one_list_only_still_ranks(self) -> None:
        bm25 = _results(["A", "B", "C"], "bm25")
        dense = _results(["C", "D"], "dense")
        fused = rrf_fuse(bm25, dense, k=60)
        assert [r.chunk_id for r in fused] == ["C", "A", "B", "D"]

    def test_ranks_are_one_based_and_contiguous(self) -> None:
        fused = rrf_fuse(_results(["A", "B", "C"], "bm25"), _results(["A", "D"], "dense"))
        assert [r.rank for r in fused] == list(range(1, len(fused) + 1))

    def test_results_are_tagged_rrf_and_carry_full_chunk_metadata(self) -> None:
        fused = rrf_fuse(_results(["A", "B"], "bm25"), _results(["B", "C"], "dense"))
        assert all(r.retriever == RRF_NAME for r in fused)
        assert all(r.chunk.allowed_roles == ("employee",) for r in fused)
        assert all(r.chunk.classification is Classification.PUBLIC for r in fused)

    def test_binary_presence_rather_than_magnitude(self) -> None:
        fused = rrf_fuse(_results(["A", "B"], "bm25"), _results(["B", "A"], "dense"))
        # Both fusions give A and B the same total weight, so tie-break on id.
        assert [r.chunk_id for r in fused] == ["A", "B"]

    def test_default_k_comes_from_settings(self) -> None:
        from hybridrag.config import get_settings

        assert get_settings().rrf_k == 60
        fused = rrf_fuse(_results(["A"], "bm25"))
        assert fused[0].score == 1.0 / 61

    def test_empty_rankings_yield_empty_result(self) -> None:
        assert rrf_fuse() == []
        assert rrf_fuse([], []) == []

    def test_non_positive_k_is_rejected(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="positive"):
            rrf_fuse(_results(["A"], "bm25"), k=0)


class FakeReranker:
    """A reranker that reorders candidates so later input ranks higher."""

    def __init__(self, model_name: str = "fake-reranker") -> None:
        self._model_name = model_name
        self.calls: list[tuple[str, list[RankedChunk]]] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(self, query: str, candidates: Sequence[RankedChunk]) -> list[RankedChunk]:
        self.calls.append((query, list(candidates)))
        # Reverse the input order so reranking visibly changes the ranking.
        return [
            RankedChunk(
                chunk=candidate.chunk,
                score=float(len(candidates) - i),
                rank=rank,
                retriever=RERANK_NAME,
            )
            for rank, (i, candidate) in enumerate(reversed(list(enumerate(candidates))), start=1)
        ]


class TestRerankTop:
    def test_bounds_candidates_before_reranking(self) -> None:
        reranker = FakeReranker()
        candidates = _results([f"C{i}" for i in range(10)], "rrf")
        out = rerank_top("query", candidates, reranker=reranker, rerank_candidates=4, final_top_k=2)
        assert reranker.calls[0][1] == candidates[:4]
        assert len(out) == 2

    def test_returns_reranked_results_tagged_cross_encoder(self) -> None:
        reranker = FakeReranker("fake-reranker-v1")
        candidates = _results(["A", "B", "C"], "rrf")
        out = rerank_top("q", candidates, reranker=reranker, rerank_candidates=3, final_top_k=3)
        assert [r.retriever for r in out] == [RERANK_NAME] * 3
        assert reranker.model_name == "fake-reranker-v1"

    def test_zero_slices_short_circuit(self) -> None:
        reranker = FakeReranker()
        candidates = _results(["A", "B"], "rrf")
        assert (
            rerank_top("q", candidates, reranker=reranker, rerank_candidates=0, final_top_k=5) == []
        )
        assert (
            rerank_top("q", candidates, reranker=reranker, rerank_candidates=5, final_top_k=0) == []
        )

    def test_empty_candidates_stay_empty(self) -> None:
        reranker = FakeReranker()
        assert rerank_top("q", [], reranker=reranker, rerank_candidates=5, final_top_k=5) == []


class TestRerankerProtocol:
    def test_fake_satisfies_the_declared_protocol(self) -> None:
        assert isinstance(FakeReranker(), Reranker)
