"""Unit tests for core domain models."""

from datetime import date

import pytest
from pydantic import ValidationError

from hybridrag.domain import (
    Chunk,
    Classification,
    Document,
    DocumentStatus,
    RankedChunk,
    SourceType,
    make_chunk_id,
)
from hybridrag.domain.models import content_hash


def _sample_chunk(chunk_index: int = 0, text: str = "Remote work is limited to 2 days.") -> Chunk:
    return Chunk(
        chunk_id=make_chunk_id("HR-003", "v1", chunk_index),
        document_id="HR-003",
        document_version="v1",
        text=text,
        chunk_index=chunk_index,
        token_count=8,
        content_hash=content_hash(text),
        section_title="3.1 Standard Remote Work Limit",
        source_type=SourceType.POLICY,
        document_type="policy",
        department="HR",
        classification=Classification.PUBLIC,
        allowed_roles=("employee", "manager", "hr", "finance", "it", "admin"),
        allowed_departments=("*",),
        effective_date=date(2025, 1, 1),
    )


class TestChunkId:
    def test_format(self) -> None:
        assert make_chunk_id("HR-003", "v2", 7) == "HR-003:v2:0007"

    def test_reproducible(self) -> None:
        assert make_chunk_id("FIN-002", "v1", 0) == make_chunk_id("FIN-002", "v1", 0)

    def test_unique_across_versions(self) -> None:
        assert make_chunk_id("HR-003", "v1", 0) != make_chunk_id("HR-003", "v2", 0)

    def test_unique_across_chunks_of_same_document(self) -> None:
        ids = {make_chunk_id("HR-003", "v1", i) for i in range(100)}
        assert len(ids) == 100


class TestContentHash:
    def test_deterministic(self) -> None:
        assert content_hash("abc") == content_hash("abc")

    def test_changes_with_text(self) -> None:
        assert content_hash("abc") != content_hash("abd")


class TestDocument:
    def test_valid_document(self) -> None:
        doc = Document(
            document_id="HR-003",
            title="Remote Work Policy",
            source_type=SourceType.POLICY,
            document_type="policy",
            department="HR",
            classification=Classification.PUBLIC,
            allowed_roles=("employee", "admin"),
            document_version="v1",
            status=DocumentStatus.ACTIVE,
            source_uri="data/raw/policies/hr/HR-003_remote_work_policy_v1.md",
            checksum="0" * 64,
        )
        assert doc.tenant_id == "nexacore"

    def test_invalid_classification_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Document(
                document_id="HR-003",
                title="X",
                source_type=SourceType.POLICY,
                document_type="policy",
                classification="top_secret",  # type: ignore[arg-type]
                allowed_roles=("admin",),
                source_uri="x",
                checksum="0" * 64,
            )

    def test_frozen(self) -> None:
        doc = Document(
            document_id="HR-003",
            title="X",
            source_type=SourceType.POLICY,
            document_type="policy",
            classification=Classification.PUBLIC,
            allowed_roles=("admin",),
            source_uri="x",
            checksum="0" * 64,
        )
        with pytest.raises(ValidationError):
            doc.title = "Y"  # type: ignore[misc]


class TestChunk:
    def test_chunk_carries_authorization_metadata(self) -> None:
        chunk = _sample_chunk()
        assert chunk.classification is Classification.PUBLIC
        assert "admin" in chunk.allowed_roles
        assert chunk.chunk_id == "HR-003:v1:0000"

    def test_frozen(self) -> None:
        chunk = _sample_chunk()
        with pytest.raises(ValidationError):
            chunk.text = "tampered"  # type: ignore[misc]


class TestRankedChunk:
    def test_exposes_chunk_id_for_fusion(self) -> None:
        ranked = RankedChunk(chunk=_sample_chunk(), score=12.5, rank=1, retriever="bm25")
        assert ranked.chunk_id == "HR-003:v1:0000"
