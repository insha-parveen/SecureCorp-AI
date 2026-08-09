"""Core domain models for documents, chunks, and retrieval results.

These models are the normalized representation shared by ingestion, BM25
indexing, dense (ChromaDB) indexing, retrieval, authorization, and evaluation.
They must remain independent of any specific vector store, search library,
web framework, or LLM provider.
"""

import hashlib
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Classification(StrEnum):
    """Document sensitivity levels (Company Bible §7)."""

    PUBLIC = "public"
    DEPARTMENT_INTERNAL = "department_internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class DocumentStatus(StrEnum):
    """Lifecycle status of a document version (Company Bible §6)."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class SourceType(StrEnum):
    """Origin type of a corpus document; drives chunking strategy selection."""

    POLICY = "policy"
    KNOWLEDGE_BASE = "knowledge_base"
    EMAIL = "email"
    MEETING = "meeting"
    SLACK = "slack"
    JIRA = "jira"
    GITHUB = "github"


class Document(BaseModel):
    """Normalized document metadata (Company Bible §6a).

    Heterogeneous source frontmatter (``email_id``, ``meeting_id``,
    ``issue_id``, ...) is normalized into ``document_id`` at ingestion time.
    Source-specific fields that don't fit here are preserved in ``metadata``.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str
    title: str
    source_type: SourceType
    document_type: str  # e.g. policy | sop | project_doc | issue | transcript
    department: str | None = None
    classification: Classification
    allowed_roles: tuple[str, ...]
    allowed_departments: tuple[str, ...] = ()
    owner_user_id: str | None = None
    tenant_id: str = "nexacore"
    document_version: str = "v1"
    effective_date: date | None = None
    created_date: date | None = None
    status: DocumentStatus = DocumentStatus.ACTIVE
    source_uri: str  # repo-relative path of the raw file
    checksum: str  # sha256 of the raw file content
    word_count: int = 0  # whitespace word count of the body (ingestion stat)
    estimated_tokens: int = 0  # ~1.3 tokens/word heuristic (ingestion stat)
    metadata: dict[str, Any] = Field(default_factory=dict)


def make_chunk_id(document_id: str, document_version: str, chunk_index: int) -> str:
    """Build the stable, reproducible, globally unique chunk identifier.

    Format: ``{document_id}:{document_version}:{chunk_index:04d}``.
    RRF fusion and citation resolution operate on this ID.
    """
    return f"{document_id}:{document_version}:{chunk_index:04d}"


def content_hash(text: str) -> str:
    """Deterministic sha256 hash of chunk text (integrity / change detection)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Chunk(BaseModel):
    """Normalized chunk shared by the BM25 and dense indexes.

    Carries full authorization and provenance metadata so filtering can be
    enforced at the retrieval boundary and citations resolve to real evidence.
    """

    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document_id: str
    document_version: str
    text: str
    chunk_index: int
    token_count: int
    content_hash: str
    section_title: str | None = None
    page_number: int | None = None
    # Inherited authorization / provenance metadata
    source_type: SourceType
    document_type: str
    department: str | None = None
    classification: Classification
    allowed_roles: tuple[str, ...]
    allowed_departments: tuple[str, ...] = ()
    owner_user_id: str | None = None
    tenant_id: str = "nexacore"
    effective_date: date | None = None
    status: DocumentStatus = DocumentStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class RankedChunk(BaseModel):
    """A chunk with a retrieval score — the common result model that BM25 and
    dense retrieval both return, enabling RRF fusion over ``chunk_id``.
    """

    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    score: float
    rank: int  # 1-based rank within its source ranking
    retriever: str  # "bm25" | "dense" | "rrf" | "cross_encoder"

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id


class StructuredAnswer(BaseModel):
    """The expected JSON format from the LLM.

    Used to separate the final answer from the cited evidence ranks.
    """
    answer: str
    citations: list[int] = Field(default_factory=list)


class FinalResponse(BaseModel):
    """The final output of the RAG system.

    Includes the generated answer, the validated citations, and
    the evidence used for provenance and UI display.
    """
    model_config = ConfigDict(frozen=True)

    answer: str
    evidence: list[RankedChunk]
    citations: list[int]
    model: str
    usage: dict[str, float | int]
