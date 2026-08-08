"""Integration tests for the real ChromaDB adapter.

The unit tests use an in-memory fake, which proves the pipeline's logic but not
that Chroma actually accepts our metadata shape or honours upsert-by-id. These
tests run against a real persistent collection in a temporary directory, with
fake vectors — so they exercise the SDK without downloading an embedding model.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from hybridrag.indexing import ChromaVectorStore, VectorRecord, VectorStore, encode_chunk
from tests.unit.test_indexing import MODEL, FakeEmbeddings, _chunk

chromadb = pytest.importorskip("chromadb", reason="retrieval extra not installed")


@pytest.fixture
def store(tmp_path: Path) -> Iterator[ChromaVectorStore]:
    yield ChromaVectorStore(tmp_path / "chroma", "test_chunks")


def _record(index: int, text: str) -> VectorRecord:
    chunk = _chunk(index, text)
    return VectorRecord(
        id=chunk.chunk_id,
        text=chunk.text,
        metadata=encode_chunk(chunk, embedding_model=MODEL, corpus_version="test-v1"),
        embedding=FakeEmbeddings()._vector(text),
    )


class TestChromaAdapter:
    def test_satisfies_the_vector_store_protocol(self, store: ChromaVectorStore) -> None:
        assert isinstance(store, VectorStore)

    def test_upsert_then_read_back_metadata(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text"), _record(1, "beta text")])
        stored = store.get_metadata()
        assert set(stored) == {"HR-003:v1:0000", "HR-003:v1:0001"}
        assert stored["HR-003:v1:0000"]["allowed_roles"] == "employee|hr|admin"
        assert store.count() == 2

    def test_upsert_is_idempotent_by_id(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text")])
        store.upsert([_record(0, "alpha text revised")])
        assert store.count() == 1

    def test_query_returns_the_nearest_record(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text"), _record(1, "a much longer beta passage here")])
        matches = store.query(FakeEmbeddings()._vector("alpha text"), top_k=2)
        assert matches[0].id == "HR-003:v1:0000"
        assert matches[0].text == "alpha text"
        assert matches[0].distance <= matches[1].distance

    def test_metadata_filter_constrains_results(self, store: ChromaVectorStore) -> None:
        # The hook the Phase 5 authorization layer will use.
        store.upsert([_record(0, "alpha text"), _record(1, "beta text")])
        matches = store.query(
            FakeEmbeddings()._vector("alpha text"),
            top_k=5,
            where={"chunk_index": 1},
        )
        assert [m.id for m in matches] == ["HR-003:v1:0001"]

    def test_delete_by_id(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text"), _record(1, "beta text")])
        store.delete(["HR-003:v1:0000"])
        assert set(store.get_metadata()) == {"HR-003:v1:0001"}

    def test_delete_document_removes_every_chunk(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text"), _record(1, "beta text")])
        store.delete_document("HR-003")
        assert store.count() == 0

    def test_health_reports_the_collection(self, store: ChromaVectorStore) -> None:
        store.upsert([_record(0, "alpha text")])
        health = store.health()
        assert health["backend"] == "chromadb"
        assert health["space"] == "cosine"
        assert health["count"] == 1

    def test_persistence_across_client_instances(self, tmp_path: Path) -> None:
        path = tmp_path / "chroma"
        ChromaVectorStore(path, "test_chunks").upsert([_record(0, "alpha text")])
        assert ChromaVectorStore(path, "test_chunks").count() == 1
