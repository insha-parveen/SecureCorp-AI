"""Unit tests for BM25 sparse retrieval.

Synthetic chunks pin the analyzer and ranking contract; the real-corpus tests
assert the property BM25 was added for — an exact enterprise identifier lands on
the one chunk that contains it, which dense retrieval failed to do.
"""

from datetime import date
from pathlib import Path

import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.domain import Chunk, Classification, SourceType, content_hash, make_chunk_id
from hybridrag.indexing import BM25Index, analyze

CHUNK_FILE = Path(__file__).resolve().parents[2] / "data" / "processed" / "chunks.jsonl"

needs_corpus = pytest.mark.skipif(not CHUNK_FILE.exists(), reason="chunks.jsonl not built")

# Privileged user with the IT department (the corpus stores it as "ITSEC")
# so that the corpus's restricted chunks (e.g. the LAP-220 email) are visible.
DUMMY_USER = UserContext(
    user_id="test_user",
    roles=("employee", "manager", "hr", "admin"),
    department="ITSEC",
    tenant_id="nexacore",
)


def _chunk(index: int, text: str, *, document_id: str = "DOC-1") -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id(document_id, "v1", index),
        document_id=document_id,
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
        tenant_id="nexacore",
        effective_date=date(2025, 1, 1),
    )


class TestAnalyze:
    def test_terms_are_lowercased(self) -> None:
        assert analyze("Remote Work Policy") == ["remote", "work", "policy"]

    def test_punctuation_is_dropped(self) -> None:
        # Use words that are NOT in the stopword set so we exercise punctuation
        # handling without coupling to the stopword list.
        assert analyze("approved, billed, paid.") == ["approved", "billed", "paid"]

    def test_compound_identifier_is_kept_whole(self) -> None:
        assert "inv-2026-0108" in analyze("See invoice INV-2026-0108 for details.")

    def test_compound_identifier_also_emits_its_parts(self) -> None:
        # So "EMP 0104" and a partial recall of the ID still retrieve.
        terms = analyze("EMP-0104")
        assert terms == ["emp-0104", "emp", "0104"]

    def test_simple_words_are_not_duplicated(self) -> None:
        assert analyze("policy") == ["policy"]

    def test_empty_text_has_no_terms(self) -> None:
        assert analyze("   ") == []


class TestRankingContract:
    def _index(self) -> BM25Index:
        return BM25Index(
            [
                _chunk(0, "Employees may work remotely up to 2 days per week."),
                _chunk(1, "Invoice INV-2026-0108 was approved by Finance."),
                _chunk(2, "The procurement policy covers vendor onboarding."),
            ]
        )

    def test_ranks_are_one_based_and_contiguous(self) -> None:
        results = self._index().search("policy vendor onboarding", user_context=DUMMY_USER)
        assert [r.rank for r in results] == list(range(1, len(results) + 1))

    def test_results_are_tagged_with_the_retriever(self) -> None:
        results = self._index().search("remote work", user_context=DUMMY_USER)
        assert results
        assert all(r.retriever == "bm25" for r in results)

    def test_scores_are_descending(self) -> None:
        results = self._index().search("policy invoice remotely", user_context=DUMMY_USER)
        assert [r.score for r in results] == sorted((r.score for r in results), reverse=True)

    def test_chunks_sharing_no_term_are_excluded(self) -> None:
        # Padding the result list would feed pure noise into RRF downstream.
        results = self._index().search("remotely", user_context=DUMMY_USER)
        assert [r.chunk_id for r in results] == ["DOC-1:v1:0000"]

    def test_top_n_bounds_the_result_size(self) -> None:
        results = self._index().search("policy invoice remotely", user_context=DUMMY_USER, top_n=2)
        assert len(results) == 2

    def test_non_positive_top_n_returns_nothing(self) -> None:
        assert self._index().search("policy", user_context=DUMMY_USER, top_n=0) == []

    def test_query_with_no_indexable_terms_returns_nothing(self) -> None:
        assert self._index().search("!!! ???", user_context=DUMMY_USER) == []

    def test_unknown_query_terms_return_nothing(self) -> None:
        assert self._index().search("kubernetes helm chart", user_context=DUMMY_USER) == []

    def test_empty_corpus_is_searchable_and_empty(self) -> None:
        empty = BM25Index([])
        assert len(empty) == 0
        assert empty.search("anything", user_context=DUMMY_USER) == []

    def test_results_expose_full_authorization_metadata(self) -> None:
        # Retrieval hands these chunks to the authorization layer in Phase 5,
        # so the fields must survive the retriever intact.
        result = self._index().search("remotely", user_context=DUMMY_USER)[0]
        assert result.chunk.allowed_roles == ("employee",)
        assert result.chunk.classification is Classification.PUBLIC
        assert result.chunk.tenant_id == "nexacore"

    def test_search_is_deterministic(self) -> None:
        index = self._index()
        first = index.search("policy invoice remotely", user_context=DUMMY_USER)
        second = index.search("policy invoice remotely", user_context=DUMMY_USER)
        assert [(r.chunk_id, r.score, r.rank) for r in first] == [
            (r.chunk_id, r.score, r.rank) for r in second
        ]

    def test_ties_break_on_chunk_id_not_insertion_order(self) -> None:
        index = BM25Index([_chunk(1, "identical text"), _chunk(0, "identical text")])
        assert [r.chunk_id for r in index.search("identical text", user_context=DUMMY_USER)] == [
            "DOC-1:v1:0000",
            "DOC-1:v1:0001",
        ]


class TestExactIdentifierRetrieval:
    def test_identifier_query_outranks_a_topically_similar_chunk(self) -> None:
        index = BM25Index(
            [
                _chunk(0, "Invoice INV-2026-0108 totals 45,000 INR and is approved."),
                _chunk(1, "Invoices are approved by Finance within five business days."),
                _chunk(2, "Invoice INV-2026-0109 totals 12,000 INR and is pending."),
            ]
        )
        results = index.search("INV-2026-0108", user_context=DUMMY_USER)
        assert results[0].chunk_id == "DOC-1:v1:0000"

    def test_a_near_miss_identifier_does_not_win(self) -> None:
        # Four near-identical chunks: only the ID distinguishes them, and IDF
        # needs a corpus of >2 to give a df=1 term any positive weight at all.
        index = BM25Index(
            [
                _chunk(0, "Purchase order PO-8491 was raised for laptops."),
                _chunk(1, "Purchase order PO-8492 was raised for monitors."),
                _chunk(2, "Purchase order PO-8493 was raised for headsets."),
                _chunk(3, "Purchase order PO-8494 was raised for docks."),
            ]
        )
        assert index.search("PO-8492", user_context=DUMMY_USER)[0].chunk_id == "DOC-1:v1:0001"


class TestLookupAndStats:
    def test_get_returns_the_indexed_chunk(self) -> None:
        index = BM25Index([_chunk(0, "some policy text")])
        assert index.get("DOC-1:v1:0000") is not None
        assert index.get("DOC-1:v1:9999") is None

    def test_stats_report_corpus_shape(self) -> None:
        index = BM25Index([_chunk(0, "alpha beta"), _chunk(1, "beta gamma")])
        stats = index.stats
        assert stats["chunks"] == 2
        assert stats["documents"] == 1
        assert stats["vocabulary"] == 3
        assert stats["terms_total"] == 4

    def test_bm25_parameters_are_configurable(self) -> None:
        index = BM25Index([_chunk(0, "alpha")], k1=1.2, b=0.5)
        assert index.stats["k1"] == 1.2
        assert index.stats["b"] == 0.5


@pytest.fixture(scope="module")
def index() -> BM25Index:
    """The real corpus index, built once for the whole module."""
    return BM25Index.from_chunk_file(CHUNK_FILE)


@needs_corpus
class TestRealCorpus:
    def test_index_covers_the_whole_chunk_corpus(self, index: BM25Index) -> None:
        assert len(index) == index.stats["chunks"]
        assert len(index) > 400

    def test_purchase_order_id_retrieves_its_own_chunk(self, index: BM25Index) -> None:
        # PO-9102 appears in exactly one chunk of the corpus.
        assert (
            index.search("PO-9102", user_context=DUMMY_USER)[0].chunk_id
            == "EMAIL-2026-0040:v1:0000"
        )

    def test_asset_tag_retrieves_its_own_chunk(self, index: BM25Index) -> None:
        assert (
            index.search("LAP-220", user_context=DUMMY_USER)[0].chunk_id
            == "EMAIL-2026-0085:v1:0000"
        )

    def test_natural_language_query_retrieves_the_remote_work_policy(
        self, index: BM25Index
    ) -> None:
        results = index.search(
            "how many days per week can I work remotely",
            user_context=DUMMY_USER,
            top_n=10,
        )
        assert any(r.chunk.document_id == "HR-003" for r in results)

    def test_every_result_resolves_back_through_get(self, index: BM25Index) -> None:
        for result in index.search("security incident response", user_context=DUMMY_USER, top_n=10):
            assert index.get(result.chunk_id) == result.chunk
