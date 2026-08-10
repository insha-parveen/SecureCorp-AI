"""Unit tests for the Phase 8 citation-metrics module."""

from __future__ import annotations

import pytest

from hybridrag.domain import Chunk, Classification, FinalResponse, RankedChunk, SourceType
from hybridrag.evaluation.citation_metrics import compute_citation_metrics


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


def _make_response(answer: str, citations: list[int], n_evidence: int = 3) -> FinalResponse:
    evidence = [
        RankedChunk(chunk=_make_chunk(f"D{i}", i), score=0.9, rank=i + 1, retriever="bm25")
        for i in range(n_evidence)
    ]
    return FinalResponse(
        answer=answer,
        evidence=evidence,
        citations=citations,
        model="test-model",
        usage={},
    )


def test_empty_iterable_yields_zero_metrics() -> None:
    m = compute_citation_metrics(iter([]))
    assert m.n_items == 0
    assert m.valid_citation_rate == 0.0
    assert m.invalid_citation_rate == 0.0
    assert m.citation_coverage == 0.0


def test_all_citations_valid() -> None:
    pairs = [({"id": "1"}, _make_response("per HR-002, 18 days", [1, 2]))]
    m = compute_citation_metrics(pairs)
    assert m.n_items == 1
    assert m.n_abstentions == 0
    assert m.valid_citation_rate == 1.0
    assert m.invalid_citation_rate == 0.0
    assert m.n_with_citations == 1
    assert m.citation_coverage == 1.0


def test_citation_out_of_range_treated_as_invalid() -> None:
    # 4 evidence chunks, citations [1, 2, 9] — 9 is out of range
    pairs = [({"id": "1"}, _make_response("answer", [1, 2, 9], n_evidence=4))]
    m = compute_citation_metrics(pairs)
    assert m.valid_citation_rate == pytest.approx(2 / 3)
    assert m.invalid_citation_rate == pytest.approx(1 / 3)


def test_abstention_excluded_from_coverage_and_rates() -> None:
    pairs = [
        (
            {"id": "1"},
            _make_response(
                "I cannot answer that question as it is outside my scope.",
                [],
            ),
        ),
        ({"id": "2"}, _make_response("per HR-002, 18 days", [1])),
    ]
    m = compute_citation_metrics(pairs)
    assert m.n_items == 2
    assert m.n_abstentions == 1
    # Coverage denominator = 1 (only the answered item)
    assert m.n_with_citations == 1
    assert m.citation_coverage == 1.0
    # Citation rate denominator = 1 (only the answered item had citations)
    assert m.valid_citation_rate == 1.0


def test_no_citations_but_answered_set_rate_to_zero() -> None:
    pairs = [
        ({"id": "1"}, _make_response("Sure, the answer is 42.", [], n_evidence=3)),
    ]
    m = compute_citation_metrics(pairs)
    assert m.n_items == 1
    assert m.n_abstentions == 0
    assert m.n_with_citations == 0
    assert m.citation_coverage == 0.0
    # No citation signal → rate stays 0.0 (not NaN)
    assert m.valid_citation_rate == 0.0
    assert m.invalid_citation_rate == 0.0


def test_expected_abstain_predicate_excludes_items() -> None:
    """A custom abstention predicate can use the golden row's expected_abstain."""
    golden = {"id": "1", "expected_abstain": True}
    resp = _make_response("I do not know the answer to that.", [1])
    pairs = [(golden, resp)]

    def predicate(g: dict, r: FinalResponse) -> bool:
        return bool(g.get("expected_abstain", False))

    m = compute_citation_metrics(pairs, abstain_predicate=predicate)
    assert m.n_abstentions == 1
    assert m.n_with_citations == 0
    assert m.citation_coverage == 0.0


def test_aggregation_across_many_items() -> None:
    pairs = [
        ({"id": "1"}, _make_response("answer-1", [1, 2])),  # 2/2 valid
        ({"id": "2"}, _make_response("answer-2", [1, 2, 3])),  # 3/3 valid
        ({"id": "3"}, _make_response("answer-3", [1, 9], n_evidence=4)),  # 1/2 valid
    ]
    m = compute_citation_metrics(pairs)
    # Per-item average: (1.0 + 1.0 + 0.5) / 3 = 5/6
    assert m.valid_citation_rate == pytest.approx(5 / 6)
    assert m.invalid_citation_rate == pytest.approx(1 / 6)
    assert m.n_with_citations == 3
    assert m.citation_coverage == 1.0
