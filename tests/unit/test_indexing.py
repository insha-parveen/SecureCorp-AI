"""Unit tests for the dense indexing pipeline.

Everything here runs against fakes: a deterministic embedding provider and an
in-memory vector store. That is deliberate — the pipeline's contract (what gets
re-embedded, what gets pruned, what metadata survives) must be testable without
downloading a model or writing to data/chroma_db/.
"""

from collections.abc import Sequence
from datetime import date
from typing import Any

import pytest

from hybridrag.domain import Chunk, Classification, DocumentStatus, SourceType
from hybridrag.indexing import (
    EmbeddingProvider,
    VectorMatch,
    VectorRecord,
    VectorStore,
    decode_chunk,
    encode_chunk,
    index_chunks,
)

MODEL = "fake-embeddings-v1"


class FakeEmbeddings:
    """Deterministic 4-dimensional embeddings; counts the texts it embeds."""

    def __init__(self, model_name: str = MODEL) -> None:
        self._model_name = model_name
        self.calls: list[list[str]] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return 4

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        return [float(len(text)), float(text.count(" ")), float(sum(map(ord, text[:8]))), 1.0]

    @property
    def embedded_count(self) -> int:
        return sum(len(batch) for batch in self.calls)


class InMemoryStore:
    """Minimal VectorStore implementation backed by a dict."""

    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        for record in records:
            self.records[record.id] = record

    def delete(self, ids: Sequence[str]) -> None:
        for record_id in ids:
            self.records.pop(record_id, None)

    def get_metadata(self, ids: Sequence[str] | None = None) -> dict[str, dict[str, Any]]:
        wanted = set(ids) if ids is not None else set(self.records)
        return {k: dict(v.metadata) for k, v in self.records.items() if k in wanted}

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        return [
            VectorMatch(id=r.id, text=r.text, metadata=dict(r.metadata), distance=0.0)
            for r in list(self.records.values())[:top_k]
        ]

    def count(self) -> int:
        return len(self.records)

    def health(self) -> dict[str, Any]:
        return {"backend": "memory", "count": self.count()}


def _chunk(
    index: int = 0, text: str = "remote work is allowed 2 days per week", **kw: Any
) -> Chunk:
    base: dict[str, Any] = {
        "chunk_id": f"HR-003:v1:{index:04d}",
        "document_id": "HR-003",
        "document_version": "v1",
        "text": text,
        "chunk_index": index,
        "token_count": 12,
        "content_hash": f"hash-{text}",
        "section_title": "Remote Work Policy > 3. Framework",
        "source_type": SourceType.POLICY,
        "document_type": "policy",
        "department": "HR",
        "classification": Classification.DEPARTMENT_INTERNAL,
        "allowed_roles": ("employee", "hr", "admin"),
        "allowed_departments": ("HR", "Engineering"),
        "effective_date": date(2026, 1, 1),
        "metadata": {"title": "Remote Work Policy", "section_titles": ["A", "B"]},
    }
    return Chunk(**{**base, **kw})


def _index(chunks: list[Chunk], store: InMemoryStore, provider: EmbeddingProvider, **kw: Any):
    return index_chunks(
        chunks, store=store, provider=provider, corpus_version="test-corpus-v1", **kw
    )


class TestProtocolConformance:
    def test_fakes_satisfy_the_declared_protocols(self) -> None:
        # If the fakes drift from the protocols, the tests below stop proving
        # anything about the real implementations.
        assert isinstance(FakeEmbeddings(), EmbeddingProvider)
        assert isinstance(InMemoryStore(), VectorStore)


class TestChunkMetadataCodec:
    def test_round_trip_preserves_every_field(self) -> None:
        chunk = _chunk(owner_user_id="EMP-0104")
        meta = encode_chunk(chunk, embedding_model=MODEL, corpus_version="test-corpus-v1")
        assert decode_chunk(chunk.text, meta) == chunk

    def test_round_trip_with_all_optional_fields_absent(self) -> None:
        chunk = _chunk(
            section_title=None,
            department=None,
            owner_user_id=None,
            effective_date=None,
            allowed_departments=(),
            metadata={},
        )
        meta = encode_chunk(chunk, embedding_model=MODEL, corpus_version="test-corpus-v1")
        assert "section_title" not in meta  # stores reject None values
        assert decode_chunk(chunk.text, meta) == chunk

    def test_metadata_values_are_scalars_only(self) -> None:
        meta = encode_chunk(_chunk(), embedding_model=MODEL, corpus_version="v")
        assert all(isinstance(v, str | int | float | bool) for v in meta.values())

    def test_authorization_fields_survive_encoding(self) -> None:
        chunk = _chunk(allowed_roles=("hr", "admin"), classification=Classification.CONFIDENTIAL)
        decoded = decode_chunk(
            chunk.text, encode_chunk(chunk, embedding_model=MODEL, corpus_version="v")
        )
        assert decoded.allowed_roles == ("hr", "admin")
        assert decoded.classification is Classification.CONFIDENTIAL
        assert decoded.status is DocumentStatus.ACTIVE

    def test_index_provenance_is_stamped(self) -> None:
        meta = encode_chunk(_chunk(), embedding_model=MODEL, corpus_version="test-corpus-v1")
        assert meta["embedding_model"] == MODEL
        assert meta["corpus_version"] == "test-corpus-v1"


class TestIndexing:
    def test_first_run_embeds_and_stores_every_chunk(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(5)]
        store, provider = InMemoryStore(), FakeEmbeddings()
        report = _index(chunks, store, provider)
        assert report.embedded == 5
        assert report.skipped == 0
        assert store.count() == 5
        assert provider.embedded_count == 5

    def test_stored_record_carries_text_metadata_and_vector(self) -> None:
        store, provider = InMemoryStore(), FakeEmbeddings()
        chunk = _chunk()
        _index([chunk], store, provider)
        record = store.records[chunk.chunk_id]
        assert record.text == chunk.text
        assert record.embedding == provider.embed_query(chunk.text)
        assert decode_chunk(record.text, record.metadata) == chunk

    def test_rerun_on_an_unchanged_corpus_embeds_nothing(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(5)]
        store, provider = InMemoryStore(), FakeEmbeddings()
        _index(chunks, store, provider)
        second = _index(chunks, store, FakeEmbeddings())
        assert second.embedded == 0
        assert second.skipped == 5
        assert second.up_to_date

    def test_only_changed_chunks_are_re_embedded(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(4)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings())

        edited = [*chunks[:2], _chunk(2, "text number 2 — revised"), chunks[3]]
        provider = FakeEmbeddings()
        report = _index(edited, store, provider)
        assert report.embedded == 1
        assert report.skipped == 3
        assert provider.calls == [["text number 2 — revised"]]

    def test_changing_the_embedding_model_re_embeds_everything(self) -> None:
        # Vectors from two models live in different spaces; mixing them inside
        # one collection would silently corrupt similarity search.
        chunks = [_chunk(i, f"text number {i}") for i in range(3)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings("model-a"))
        report = _index(chunks, store, FakeEmbeddings("model-b"))
        assert report.embedded == 3
        assert report.embedding_model == "model-b"

    def test_force_re_embeds_without_any_corpus_change(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(3)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings())
        assert _index(chunks, store, FakeEmbeddings(), force=True).embedded == 3

    def test_removed_chunks_are_pruned_from_the_index(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(4)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings())
        report = _index(chunks[:2], store, FakeEmbeddings())
        assert report.deleted == 2
        assert set(store.records) == {"HR-003:v1:0000", "HR-003:v1:0001"}

    def test_no_prune_keeps_stale_records(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(4)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings())
        report = _index(chunks[:2], store, FakeEmbeddings(), prune=False)
        assert report.deleted == 0
        assert store.count() == 4

    def test_batching_splits_work_without_losing_chunks(self) -> None:
        chunks = [_chunk(i, f"text number {i}") for i in range(7)]
        store, provider = InMemoryStore(), FakeEmbeddings()
        _index(chunks, store, provider, batch_size=3)
        assert [len(batch) for batch in provider.calls] == [3, 3, 1]
        assert store.count() == 7

    def test_indexing_an_empty_corpus_is_a_no_op(self) -> None:
        store, provider = InMemoryStore(), FakeEmbeddings()
        report = _index([], store, provider)
        assert (report.embedded, report.deleted, store.count()) == (0, 0, 0)

    def test_chunk_ids_stay_unique_keys(self) -> None:
        # RRF fuses on chunk_id, so one stored record per chunk_id is a hard
        # requirement, not an implementation detail.
        chunks = [_chunk(i, f"text number {i}") for i in range(5)]
        store = InMemoryStore()
        _index(chunks, store, FakeEmbeddings())
        _index(chunks, store, FakeEmbeddings(), force=True)
        assert store.count() == 5


class TestEmbeddingProviderFactory:
    def test_factory_reads_the_configured_model_name(self) -> None:
        from hybridrag.config import Settings
        from hybridrag.indexing import get_embedding_provider

        settings = Settings(embedding_model="sentence-transformers/all-mpnet-base-v2")
        # No model is loaded: construction is lazy, so this stays offline.
        assert get_embedding_provider(settings).model_name == (
            "sentence-transformers/all-mpnet-base-v2"
        )


@pytest.mark.parametrize("prefix", ["", "passage: "])
def test_document_prefix_is_applied_to_passages(prefix: str) -> None:
    from hybridrag.indexing import SentenceTransformerEmbeddings

    provider = SentenceTransformerEmbeddings("unused", document_prefix=prefix)
    seen: list[list[str]] = []
    provider._encode = lambda texts: (seen.append(texts), [[0.0]] * len(texts))[1]  # type: ignore[method-assign]
    provider.embed_documents(["hello"])
    assert seen == [[prefix + "hello"]]
