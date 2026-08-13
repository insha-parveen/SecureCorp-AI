"""Chat route: ``POST /api/chat`` — Server-Sent Events.

The response is a ``text/event-stream`` of typed events. The event names
are stable contracts the frontend depends on:

- ``meta``     — pipeline telemetry (route + cache_tier), BEFORE evidence.
- ``evidence`` — one event per retrieved evidence chunk, BEFORE tokens.
- ``token``    — incremental text fragments from the LLM.
- ``done``     — the terminal event; carries the validated ``FinalResponse``.
- ``error``    — emitted on assistant errors so the frontend can render
                 a typed error card (never an opaque 500 on the stream).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from hybridrag.api.auth import current_user_from_cookie
from hybridrag.api.rate_limit import rate_limit
from hybridrag.api.schemas import (
    ChatRequest,
    DoneEventModel,
    EvidenceEventModel,
    MetaEventModel,
)
from hybridrag.assistant import (
    DoneEvent,
    EvidenceEvent,
    MetaEvent,
    TokenEvent,
)
from hybridrag.authorization.models import UserContext
from hybridrag.domain import FinalResponse, RankedChunk

router = APIRouter(prefix="/api/chat", tags=["chat"])

# MVP caveat, surfaced in the API contract: cached answers carry no
# evidence or citations. Documented so the frontend can render the
# distinction (no [1] [2] chips for cache hits).
CACHE_HIT_NOTE = (
    "Cache hits return no evidence and no citations in the MVP. "
    "Cached answers are stored as bare strings today."
)


def _evidence_to_model(rank: int, rc: RankedChunk) -> EvidenceEventModel:
    """Convert a ``RankedChunk`` to its public ``EvidenceEventModel``."""
    chunk = rc.chunk
    excerpt = chunk.text[:240]
    # The chunk's metadata carries the real document title (set at chunking
    # time from the registry Document.title). Fall back to the document_id
    # only if the title is somehow absent.
    document_title = str(chunk.metadata.get("title") or chunk.document_id)
    return EvidenceEventModel(
        rank=rank,
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        document_title=document_title,
        section_title=chunk.section_title,
        excerpt=excerpt,
    )


def _final_to_done_model(response: FinalResponse) -> DoneEventModel:
    """Convert a ``FinalResponse`` to its public ``DoneEventModel``."""
    return DoneEventModel(
        answer=response.answer,
        citations=response.citations,
        evidence=[_evidence_to_model(rank, rc) for rank, rc in enumerate(response.evidence, 1)],
        model=response.model,
        usage=response.usage,
        extras={"note": CACHE_HIT_NOTE} if not response.evidence else {},
    )


@router.post("")
async def post_chat(
    body: ChatRequest,
    request: Request,
    user: UserContext = Depends(current_user_from_cookie()),
    _: None = Depends(rate_limit()),
) -> EventSourceResponse:
    """Stream a chat response as Server-Sent Events.

    The auth dependency verifies the JWT cookie; the user context is
    built server-side from the verified token. The request body is just
    the query string.
    """
    assistant = request.app.state.assistant

    async def event_stream() -> AsyncIterator[dict[str, str]]:
        try:
            for ev in assistant.ask_stream(body.query, user, session_id=body.session_id):
                if isinstance(ev, MetaEvent):
                    payload = MetaEventModel(route=ev.route, cache_tier=ev.cache_tier).model_dump()
                    yield {"event": "meta", "data": json.dumps(payload)}
                elif isinstance(ev, EvidenceEvent):
                    # One event per chunk, ranked 1..N.
                    for rank, rc in enumerate(ev.evidence, 1):
                        payload = _evidence_to_model(rank, rc).model_dump()
                        yield {"event": "evidence", "data": json.dumps(payload)}
                elif isinstance(ev, TokenEvent):
                    yield {"event": "token", "data": json.dumps({"text": ev.text})}
                elif isinstance(ev, DoneEvent):
                    payload = _final_to_done_model(ev.response).model_dump()
                    yield {"event": "done", "data": json.dumps(payload)}
        except Exception as exc:  # noqa: BLE001
            # Surface errors as an event so the frontend can render a card.
            yield {
                "event": "error",
                "data": json.dumps({"message": "Assistant failed", "type": type(exc).__name__}),
            }

    return EventSourceResponse(event_stream())
