"""Lossless ``Chunk`` <-> vector-store-metadata codec.

Vector stores accept only flat, scalar metadata (Chroma: ``str | int | float |
bool``, and no ``None``). The domain ``Chunk`` has tuples, dates, enums, and a
nested ``metadata`` dict, so an explicit codec is needed. It lives in its own
module for two reasons:

* it is store-agnostic — the same flattening will serve any vector store the
  project adopts later, so it must not sit inside the Chroma adapter;
* it must round-trip exactly. Dense retrieval reconstructs full ``Chunk``
  objects from the index, and those carry the authorization fields the security
  layer will filter on. A lossy encode here would become a security bug there,
  so :func:`decode_chunk` is the tested inverse of :func:`encode_chunk`.

Encoding rules:

* tuples -> ``"|"``-joined strings (``allowed_roles`` etc.). Empty tuple is
  encoded as the empty string, which decodes back to ``()``.
* dates -> ISO strings; enums -> their string values.
* ``None`` -> the key is omitted, and a missing key decodes back to ``None``.
* the nested ``metadata`` dict -> one JSON string under ``metadata_json``.
* ``text`` is NOT duplicated into metadata; it is stored as the store's
  document payload.
"""

import json
from datetime import date
from typing import Any

from hybridrag.domain import Chunk, Classification, DocumentStatus, SourceType

#: Separator for tuple-valued fields. Chosen because no role, department, or
#: tenant identifier in the corpus contains a pipe.
SEQUENCE_SEPARATOR = "|"


def _join(values: tuple[str, ...]) -> str:
    return SEQUENCE_SEPARATOR.join(values)


def _split(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split(SEQUENCE_SEPARATOR) if part)


def encode_chunk(chunk: Chunk, *, embedding_model: str, corpus_version: str) -> dict[str, Any]:
    """Flatten a chunk into scalar metadata for the vector store.

    ``embedding_model`` and ``corpus_version`` are stamped onto every record.
    They are not chunk properties but index properties: incremental indexing
    uses them to decide whether a stored vector is still valid, and the caching
    layer (Phase 7) requires corpus/model versioning in its keys.
    """
    encoded: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_version": chunk.document_version,
        "chunk_index": chunk.chunk_index,
        "token_count": chunk.token_count,
        "content_hash": chunk.content_hash,
        "source_type": chunk.source_type.value,
        "document_type": chunk.document_type,
        "classification": chunk.classification.value,
        "allowed_roles": _join(chunk.allowed_roles),
        "allowed_departments": _join(chunk.allowed_departments),
        "tenant_id": chunk.tenant_id,
        "status": chunk.status.value,
        "metadata_json": json.dumps(chunk.metadata, sort_keys=True),
        # --- index provenance, not chunk provenance ---
        "embedding_model": embedding_model,
        "corpus_version": corpus_version,
    }
    if chunk.section_title is not None:
        encoded["section_title"] = chunk.section_title
    if chunk.page_number is not None:
        encoded["page_number"] = chunk.page_number
    if chunk.department is not None:
        encoded["department"] = chunk.department
    if chunk.owner_user_id is not None:
        encoded["owner_user_id"] = chunk.owner_user_id
    if chunk.effective_date is not None:
        encoded["effective_date"] = chunk.effective_date.isoformat()
    return encoded


def decode_chunk(text: str, metadata: dict[str, Any]) -> Chunk:
    """Rebuild a ``Chunk`` from stored text plus flattened metadata."""
    effective = metadata.get("effective_date")
    return Chunk(
        chunk_id=str(metadata["chunk_id"]),
        document_id=str(metadata["document_id"]),
        document_version=str(metadata["document_version"]),
        text=text,
        chunk_index=int(metadata["chunk_index"]),
        token_count=int(metadata["token_count"]),
        content_hash=str(metadata["content_hash"]),
        section_title=_optional_str(metadata.get("section_title")),
        page_number=_optional_int(metadata.get("page_number")),
        source_type=SourceType(metadata["source_type"]),
        document_type=str(metadata["document_type"]),
        department=_optional_str(metadata.get("department")),
        classification=Classification(metadata["classification"]),
        allowed_roles=_split(str(metadata.get("allowed_roles", ""))),
        allowed_departments=_split(str(metadata.get("allowed_departments", ""))),
        owner_user_id=_optional_str(metadata.get("owner_user_id")),
        tenant_id=str(metadata.get("tenant_id", "nexacore")),
        effective_date=date.fromisoformat(str(effective)) if effective else None,
        status=DocumentStatus(metadata.get("status", DocumentStatus.ACTIVE.value)),
        metadata=json.loads(str(metadata.get("metadata_json", "{}"))),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def index_fingerprint(chunk: Chunk, *, embedding_model: str) -> str:
    """The value that decides whether a stored vector can be reused.

    A stored record is up to date when its fingerprint matches. It combines the
    chunk's ``content_hash`` with the embedding model, because identical text
    embedded by a different model is a different vector in a different space —
    reusing it would silently corrupt the index.
    """
    return f"{chunk.content_hash}:{embedding_model}"


def stored_fingerprint(metadata: dict[str, Any]) -> str:
    """The fingerprint of an already-indexed record."""
    return f"{metadata.get('content_hash', '')}:{metadata.get('embedding_model', '')}"


__all__ = [
    "SEQUENCE_SEPARATOR",
    "decode_chunk",
    "encode_chunk",
    "index_fingerprint",
    "stored_fingerprint",
]
