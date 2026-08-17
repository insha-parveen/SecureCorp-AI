"""Unit tests for the Phase 8 retrieval eval extensions.

These tests construct minimal Chunk/RankedChunk fixtures and verify the
metric math (Recall@K, MRR, nDCG@K, Precision@K, Hit@1) without spinning up
BM25, ChromaDB, or any embedding model.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.domain import Chunk, Classification, RankedChunk, SourceType
from hybridrag.evaluation.retrieval_eval import (
    RetrievalEvaluator,
    _authorized_dense,
    _ndcg_at_k,
    _precision_at_k,
)
from hybridrag.indexing.vector_store import VectorMatch


def _make_chunk(doc_id: str, idx: int = 0) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}:v1:{idx:04d}",
        document_id=doc_id,
        document_version="v1",
        text="placeholder text",
        chunk_index=idx,
        token_count=10,
        content_hash="h" * 64,
        source_type=SourceType.POLICY,
        document_type="policy",
        classification=Classification.PUBLIC,
        allowed_roles=("employee",),
    )


def _make_ranked(docs: list[str]) -> list[RankedChunk]:
    return [
        RankedChunk(chunk=_make_chunk(d, i), score=1.0 - 0.01 * i, rank=i + 1, retriever="test")
        for i, d in enumerate(docs)
    ]


# ---------- pure function tests ----------


def test_ndcg_perfect_ranking() -> None:
    expected = {"A", "B"}
    retrieved = _make_ranked(["A", "B", "X"])
    # Perfect DCG=IDG=1.0
    assert _ndcg_at_k(expected, retrieved, k=5) == pytest.approx(1.0)


def test_ndcg_partial_ranking() -> None:
    expected = {"A", "B"}
    retrieved = _make_ranked(["X", "A", "Y", "B"])
    # Position 2 → 1/log2(3); position 4 → 1/log2(5)
    dcg = 1 / math.log2(3) + 1 / math.log2(5)
    # IDCG (k=5, 2 relevant docs): positions 1 and 2
    idcg = 1 / math.log2(2) + 1 / math.log2(3)
    assert _ndcg_at_k(expected, retrieved, k=5) == pytest.approx(dcg / idcg, rel=1e-3)


def test_ndcg_no_relevant() -> None:
    expected = {"A"}
    retrieved = _make_ranked(["X", "Y", "Z"])
    assert _ndcg_at_k(expected, retrieved, k=5) == 0.0


def test_precision_at_k_basic() -> None:
    expected = {"A", "B"}
    retrieved = _make_ranked(["A", "X", "B", "Y"])
    # 2 of top 4 are relevant
    assert _precision_at_k(expected, retrieved, k=4) == pytest.approx(0.5)


def test_precision_at_k_truncation() -> None:
    expected = {"A"}
    retrieved = _make_ranked(["A", "X", "Y", "Z"])
    assert _precision_at_k(expected, retrieved, k=3) == pytest.approx(1 / 3)


# ---------- evaluator integration test on a tiny JSONL ----------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_evaluator_per_category_breakdown(tmp_path: Path) -> None:
    rows = [
        {"id": "1", "query": "q1", "expected_chunk_sources": ["A"], "category": "direct_factual"},
        {"id": "2", "query": "q2", "expected_chunk_sources": ["B"], "category": "direct_factual"},
        {"id": "3", "query": "q3", "expected_chunk_sources": ["C"], "category": "exact_identifier"},
    ]
    queries_path = tmp_path / "queries.jsonl"
    _write_jsonl(queries_path, rows)

    evaluator = RetrievalEvaluator(queries_path)

    def retrieval_fn(query: str, user: UserContext) -> list[RankedChunk]:
        # q1 → A; q2 → wrong; q3 → C.
        if "q1" in query:
            return _make_ranked(["A", "X"])
        if "q2" in query:
            return _make_ranked(["X", "Y"])
        return _make_ranked(["C", "Y"])

    detailed = evaluator.evaluate_detailed(retrieval_fn, "test-arm", k=2)
    overall = detailed.overall

    # Recall@2: q1 hit (rank 1), q2 miss, q3 hit (rank 1) → 2/3
    assert overall.recall_at_k == pytest.approx(2 / 3)
    assert overall.hits == 2
    assert overall.total == 3
    # MRR: q1 1.0, q2 0.0, q3 1.0 → 2/3
    assert overall.mrr == pytest.approx(2 / 3)
    # Hit@1: q1 yes, q2 no, q3 yes → 2/3
    assert overall.hit_at_1 == pytest.approx(2 / 3)

    # Per-category check
    assert "direct_factual" in detailed.by_category
    df = detailed.by_category["direct_factual"]
    # direct_factual has q1 (hit) + q2 (miss) → 1/2
    assert df.total == 2
    assert df.hits == 1
    assert df.recall_at_k == pytest.approx(0.5)

    # exact_identifier has q3 → 1 hit / 1 total = 1.0
    ei = detailed.by_category["exact_identifier"]
    assert ei.total == 1
    assert ei.hits == 1
    assert ei.recall_at_k == pytest.approx(1.0)


def test_evaluator_legacy_json_list_still_works(tmp_path: Path) -> None:
    rows = [
        {"query": "q1", "expected_chunk_sources": ["A"]},
        {"query": "q2", "expected_documents": ["B"]},  # legacy key
    ]
    queries_path = tmp_path / "queries.json"
    queries_path.write_text(json.dumps(rows), encoding="utf-8")

    evaluator = RetrievalEvaluator(queries_path)

    def retrieval_fn(query: str, user: UserContext) -> list[RankedChunk]:
        return _make_ranked([{"q1": "A", "q2": "B"}.get(query[0:2], "X")])

    overall = evaluator.evaluate(retrieval_fn, "test-arm", k=2)
    assert overall.total == 2
    assert overall.hits == 2


def test_evaluator_returns_zero_on_empty_set(tmp_path: Path) -> None:
    queries_path = tmp_path / "queries.jsonl"
    _write_jsonl(queries_path, [])
    evaluator = RetrievalEvaluator(queries_path)

    def fn(q: str, u: UserContext) -> list[RankedChunk]:
        return []

    overall = evaluator.evaluate(fn, "test-arm")
    assert overall.total == 0
    assert overall.recall_at_k == 0
    assert overall.mrr == 0
    assert overall.ndcg_at_k == 0
    assert overall.precision_at_k == 0
    assert overall.hit_at_1 == 0


# ---------- authorization is enforced uniformly on the dense arm ----------


class _FakeEmbeddings:
    """Minimal EmbeddingProvider stub — the vector value is irrelevant here."""

    model_name = "fake"

    def embed_query(self, text: str) -> list[float]:
        return [0.0, 0.0, 0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.0, 0.0] for _ in texts]


class _FakeStore:
    """A store that returns BOTH an authorized and a forbidden match.

    It intentionally IGNORES the ``where`` filter, so the test proves the
    ``is_authorized`` post-filter — not the Chroma where-clause — is the real
    security boundary in ``_authorized_dense``.
    """

    def __init__(self, matches: list[VectorMatch]) -> None:
        self._matches = matches

    def query(self, embedding, *, top_k, where=None):  # type: ignore[no-untyped-def]
        return self._matches[:top_k]


class _FakeBM25:
    """Resolves chunk_id -> Chunk, mirroring BM25Index.get."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._by_id = {c.chunk_id: c for c in chunks}

    def get(self, chunk_id: str) -> Chunk | None:
        return self._by_id.get(chunk_id)


def _confidential_chunk(doc_id: str, department: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}:v1:0000",
        document_id=doc_id,
        document_version="v1",
        text=f"confidential body for {department}",
        chunk_index=0,
        token_count=10,
        content_hash="h" * 64,
        source_type=SourceType.POLICY,
        document_type="policy",
        department=department,
        classification=Classification.CONFIDENTIAL,
        # Same role on both chunks so DEPARTMENT is the sole discriminator: a
        # CONFIDENTIAL chunk needs has_role AND dept_match, and the eval user is
        # department=HR, so only the HR chunk survives.
        allowed_roles=("admin",),
        allowed_departments=(department,),
    )


def test_authorized_dense_drops_unauthorized_chunk() -> None:
    """The dense ablation arm must exclude chunks the eval user can't see.

    This is the fix for the mixed-population ablation table: Dense-Only used to
    return raw ``store.query`` hits (no auth), while Hybrid-Rerank enforced auth.
    Now both go through ``_authorized_dense``.
    """
    from hybridrag.config import get_settings

    # HR-department admin: NOT authorized for a Finance-department confidential doc.
    user = UserContext(user_id="eval", roles=("admin",), department="HR", tenant_id="nexacore")

    allowed = _confidential_chunk("DOC-HR", "HR")  # dept matches -> visible
    forbidden = _confidential_chunk("DOC-FIN", "Finance")  # dept mismatch -> hidden

    def _match(c: Chunk) -> VectorMatch:
        return VectorMatch(id=c.chunk_id, text=c.text, metadata={}, distance=0.1)

    store = _FakeStore([_match(forbidden), _match(allowed)])
    bm25 = _FakeBM25([allowed, forbidden])

    result = _authorized_dense(
        "any query",
        store=store,  # type: ignore[arg-type]
        embeddings=_FakeEmbeddings(),  # type: ignore[arg-type]
        bm25=bm25,  # type: ignore[arg-type]
        user_context=user,
        settings=get_settings(),
    )

    returned_docs = {rc.chunk.document_id for rc in result}
    # The forbidden Finance chunk must be dropped by the is_authorized post-filter.
    assert returned_docs == {"DOC-HR"}
