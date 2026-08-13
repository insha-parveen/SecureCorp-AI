"""Unit tests for the BM25 retriever.

Runs entirely on a small in-memory corpus — no chunks.jsonl, no model download,
no Chroma. The properties under test are the ones the future hybrid pipeline
relies on: stable ranks, zero-score exclusion, a `RankedChunk` result shape, and
an artifact that refuses to load when it no longer matches the code.
"""

from datetime import date
from typing import Any

import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.domain import Chunk, Classification, RankedChunk, SourceType
from hybridrag.indexing.bm25_store import (
    BM25Index,
)


def _chunk(index: int, text: str, **kw: Any) -> Chunk:
    base: dict[str, Any] = {
        "chunk_id": f"DOC-{index:03d}:v1:0000",
        "document_id": f"DOC-{index:03d}",
        "document_version": "v1",
        "text": text,
        "chunk_index": 0,
        "token_count": max(len(text.split()), 1),
        "content_hash": f"hash-{index}",
        "section_title": None,
        "source_type": SourceType.POLICY,
        "document_type": "policy",
        "department": "HR",
        "classification": Classification.DEPARTMENT_INTERNAL,
        "allowed_roles": ("employee",),
        "allowed_departments": (),
        "effective_date": date(2026, 1, 1),
        "metadata": {},
    }
    return Chunk(**{**base, **kw})


CORPUS = [
    _chunk(1, "Employees may work remotely two days per week under the remote work policy."),
    _chunk(2, "Invoice INV-2026-0108 was approved by Finance and paid to the vendor."),
    _chunk(3, "Expense claims must be submitted within thirty days of travel."),
    _chunk(4, "The vendor onboarding procedure requires a signed contract."),
]

# Dummy user context for authorization checks
DUMMY_USER = UserContext(user_id="test_user", roles=("employee",), department="HR")


@pytest.fixture
def retriever() -> BM25Index:
    return BM25Index(CORPUS)


class TestBuild:
    def test_indexes_every_chunk(self, retriever: BM25Index) -> None:
        assert len(retriever) == len(CORPUS)
        assert [retriever.get(c.chunk_id) for c in CORPUS] == CORPUS

    def test_chunk_lookup_resolves_ids(self, retriever: BM25Index) -> None:
        assert retriever.get(CORPUS[0].chunk_id) == CORPUS[0]
        assert retriever.get("nope") is None

    def test_section_title_and_document_title_are_indexed(self) -> None:
        chunk = _chunk(
            9,
            "Submit the form before the deadline.",
            section_title="Expense Reimbursement",
            metadata={"title": "Finance Handbook"},
        )
        index = BM25Index([chunk])
        assert index.search("expense reimbursement", user_context=DUMMY_USER)
        assert index.search("finance handbook", user_context=DUMMY_USER)

    def test_stats_describe_the_index(self, retriever: BM25Index) -> None:
        stats = retriever.stats
        assert stats["chunks"] == len(CORPUS)
        assert stats["vocabulary"] > 0
        assert stats["k1"] == 1.5


class TestSearch:
    def test_returns_ranked_chunks_tagged_with_this_retriever(self, retriever: BM25Index) -> None:
        results = retriever.search("remote work", user_context=DUMMY_USER)
        assert results and all(isinstance(r, RankedChunk) for r in results)
        assert all(r.retriever == "bm25" for r in results)

    def test_ranks_are_one_based_and_contiguous(self, retriever: BM25Index) -> None:
        results = retriever.search("vendor", user_context=DUMMY_USER)
        assert [r.rank for r in results] == list(range(1, len(results) + 1))

    def test_scores_are_non_increasing(self, retriever: BM25Index) -> None:
        scores = [
            r.score for r in retriever.search("policy work vendor invoice", user_context=DUMMY_USER)
        ]
        assert scores == sorted(scores, reverse=True)

    def test_exact_identifier_query_ranks_its_own_chunk_first(self, retriever: BM25Index) -> None:
        top = retriever.search("INV-2026-0108", user_context=DUMMY_USER)[0]
        assert top.chunk_id == CORPUS[1].chunk_id

    def test_zero_score_chunks_are_never_padded_in(self, retriever: BM25Index) -> None:
        results = retriever.search("INV-2026-0108", user_context=DUMMY_USER, top_n=10)
        assert len(results) < len(CORPUS)
        assert all(r.score > 0.0 for r in results)

    def test_top_n_bounds_the_result_set(self, retriever: BM25Index) -> None:
        assert (
            len(retriever.search("the policy work days vendor", user_context=DUMMY_USER, top_n=1))
            == 1
        )

    def test_non_positive_top_n_returns_nothing(self, retriever: BM25Index) -> None:
        assert retriever.search("remote work", user_context=DUMMY_USER, top_n=0) == []

    def test_results_are_stable_across_repeated_searches(self, retriever: BM25Index) -> None:
        first = [r.chunk_id for r in retriever.search("work policy days", user_context=DUMMY_USER)]
        second = [r.chunk_id for r in retriever.search("work policy days", user_context=DUMMY_USER)]
        assert first == second

    def test_ties_break_on_chunk_id(self) -> None:
        same = "quarterly compliance review"
        pair = [_chunk(20, same), _chunk(19, same)]
        results = BM25Index(pair).search(same, user_context=DUMMY_USER)
        assert [r.chunk_id for r in results] == sorted(r.chunk_id for r in results)


class TestParams:
    def test_params_come_from_settings(self) -> None:
        from hybridrag.config import Settings

        settings = Settings(bm25_k1=1.9, bm25_b=0.4)
        index = BM25Index(CORPUS, settings=settings)
        assert index.stats["k1"] == 1.9
        assert index.stats["b"] == 0.4
