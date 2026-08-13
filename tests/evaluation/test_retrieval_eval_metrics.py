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
    _ndcg_at_k,
    _precision_at_k,
)


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
