"""Chat route: ``POST /api/chat`` — Server-Sent Events.

The response is a ``text/event-stream`` of typed events. The event names
are stable contracts the frontend depends on:

- ``meta``     — pipeline telemetry (route + cache_tier), BEFORE evidence.
- ``evidence`` — one event per retrieved evidence chunk, BEFORE tokens.
- ``token``    — incremental text fragments from the LLM.
- ``done``     — the terminal event; carries the validated ``FinalResponse``.
- ``error``    — emitted on assistant errors so the frontend can render
                 a typed error card (never an opaque 500 on the stream).
                 Carries ``message``, ``type``, and a truncated ``detail``
                 with the underlying reason; the full traceback is logged
                 server-side.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import iterate_in_threadpool

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# How much of the underlying exception text to forward to the client. The full
# traceback is always logged server-side; the client gets a truncated reason so
# a failure is diagnosable from the UI instead of an opaque "Assistant failed".
_ERROR_DETAIL_LIMIT = 300

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
        # ``ask_stream`` is a SYNC generator doing blocking I/O (LLM HTTP calls,
        # Redis, Chroma, the local reranker). Iterating it directly inside this
        # coroutine would block the event loop for the whole request, so tokens
        # could not be flushed as they arrive and concurrent requests would
        # stall behind this one. ``iterate_in_threadpool`` runs each ``next()``
        # in a worker thread, so every yielded event reaches the client
        # immediately and the server stays responsive while the LLM streams.
        events = iterate_in_threadpool(
            assistant.ask_stream(body.query, user, session_id=body.session_id)
        )
        try:
            async for ev in events:
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
            # Log the full traceback server-side — an opaque client-side message
            # previously made production failures (e.g. an LLM model that the
            # API key cannot access) undiagnosable from the logs.
            logger.exception(
                "chat stream failed for user=%s tenant=%s",
                user.user_id,
                user.tenant_id,
            )
            # Surface a typed error event (never an opaque 500 mid-stream) and
            # include a truncated reason so the UI can show what went wrong.
            detail = str(exc)[:_ERROR_DETAIL_LIMIT]
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message": "Assistant failed",
                        "type": type(exc).__name__,
                        "detail": detail,
                    }
                ),
            }

    return EventSourceResponse(event_stream())
