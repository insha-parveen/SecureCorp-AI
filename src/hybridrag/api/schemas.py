"""Pydantic request/response models for the API surface."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Body for ``POST /api/auth/token``."""

    user_id: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    """Response from ``/api/auth/token`` and ``/api/auth/me``.

    ``roles`` is a list of strings to be JSON-friendly; the server-side
    ``UserContext`` is built from the verified JWT, never from this body.
    """

    user_id: str
    roles: list[str]
    department: str | None
    tenant_id: str
    expires_in: int


class ChatRequest(BaseModel):
    """Body for ``POST /api/chat``."""

    query: str = Field(min_length=1, max_length=2048)
    session_id: str | None = Field(
        default=None, description="Optional session ID for conversation history."
    )


class MetaEventModel(BaseModel):
    """Pipeline telemetry, emitted before evidence/tokens.

    ``route`` is the classified route (``DOCUMENT_RAG`` / ``STRUCTURED_SQL`` /
    ``REFUSE``), or ``None`` on a cache hit where routing was skipped.
    ``cache_tier`` is ``"L1"``, ``"L2"``, or ``"MISS"``.
    """

    route: str | None = None
    cache_tier: str


class EvidenceEventModel(BaseModel):
    """One chunk of evidence in the SSE stream."""

    rank: int
    chunk_id: str
    document_id: str
    document_title: str
    section_title: str | None = None
    excerpt: str


class DoneEventModel(BaseModel):
    """The terminal ``done`` event. ``answer`` is the full text the model emitted."""

    answer: str
    citations: list[int]
    evidence: list[EvidenceEventModel]
    model: str
    usage: dict[str, float | int]
    extras: dict[str, Any] = Field(default_factory=dict)
