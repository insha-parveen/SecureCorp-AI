"""Tests for the ``/api/chat`` SSE route.

Covers (per the Phase 9 plan):
- 401 when the JWT cookie is missing.
- ``evidence`` events arrive BEFORE any ``token`` event.
- The ``done`` event carries citations that are valid ranks of the
  emitted evidence.
- An L1 cache hit emits only the terminal ``done`` event (no evidence,
  no tokens), and the documented MVP caveat is present.
- The structured-SQL and REFUSE paths emit a single ``done`` event
  with no evidence.

The tests stub the ``SecureCorpAssistant.ask_stream`` method directly,
so they do NOT require a live retriever, embeddings, or LLM.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from hybridrag.api.app import create_app
from hybridrag.api.routes_chat import CACHE_HIT_NOTE
from hybridrag.assistant import (
    DoneEvent,
    EvidenceEvent,
    MetaEvent,
    TokenEvent,
)
from hybridrag.domain import Chunk, Classification, FinalResponse, RankedChunk, SourceType


def _fake_chunk(chunk_id: str = "HR-001:v1:0001") -> Chunk:
    """Build a minimal Chunk suitable for the test assistant."""
    return Chunk(
        chunk_id=chunk_id,
        document_id=chunk_id.split(":")[0],
        document_version="v1",
        text="The remote work policy allows two days per week.",
        chunk_index=1,
        token_count=10,
        content_hash="deadbeef",
        source_type=SourceType.POLICY,
        document_type="policy",
        department="HR",
        classification=Classification.PUBLIC,
        allowed_roles=("employee", "manager", "hr"),
    )


class _StubAssistant:
    """A minimal stand-in for ``SecureCorpAssistant`` that emits scripted events.

    The real assistant wires up cache, router, generator, structured SQL, and
    a retriever — the test does not need any of that. We replace the whole
    object on ``app.state`` so the chat route picks it up.
    """

    def __init__(self, events: list[Any]) -> None:
        self._events = events

    def ask_stream(self, query: str, user_context: Any, session_id: str | None = None) -> Any:
        # Force the iterator to be consumed.
        yield from self._events


def _build_app_with_stub(events: list[Any]) -> Any:
    app = create_app()
    # Replace the assistant on app.state with the stub before the first request.
    app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]
    return app


@pytest.fixture()
def authed_client() -> TestClient:
    """A client with a valid auth cookie; the assistant is replaced per test."""
    app = create_app()
    # base_url must be http://localhost so the Domain=localhost auth cookie is
    # attached to subsequent requests (TestClient's default host is testserver).
    with TestClient(app, base_url="http://localhost") as c:
        login = c.post("/api/auth/token", json={"user_id": "alice"})
        # Domain=localhost cookies are flaky in httpx's cookie jar (no embedded
        # dot); re-attach the cookie explicitly so protected routes see it.
        cookie_value = login.cookies.get("sc_auth")
        if cookie_value is not None:
            c.cookies.set("sc_auth", cookie_value)
        yield c


def test_missing_cookie_returns_401() -> None:
    app = create_app()
    with TestClient(app) as c:
        response = c.post("/api/chat", json={"query": "What is the leave policy?"})
        assert response.status_code == 401


def test_evidence_events_come_before_tokens(authed_client: TestClient) -> None:
    chunk = _fake_chunk()
    rc = RankedChunk(chunk=chunk, score=0.9, rank=1, retriever="rrf")
    events: list[Any] = [
        EvidenceEvent(evidence=[rc]),
        TokenEvent(text="The "),
        TokenEvent(text="policy "),
        TokenEvent(text="allows remote work."),
        DoneEvent(
            response=FinalResponse(
                answer="The policy allows remote work.",
                evidence=[rc],
                citations=[1],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    # Swap the assistant in the running app.
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "remote work?"}) as r:
        assert r.status_code == 200
        seen: list[tuple[str, str]] = []
        for line in r.iter_lines():
            if not line or not line.startswith("event:"):
                continue
            event = line[len("event:") :].strip()
            seen.append((event, ""))
        # Order: evidence -> token* -> done
        order = [e for e, _ in seen]
        assert order[0] == "evidence"
        assert "token" in order
        assert order[-1] == "done"
        # No evidence AFTER a token.
        first_token_idx = order.index("token")
        last_evidence_idx = max((i for i, e in enumerate(order) if e == "evidence"), default=-1)
        assert last_evidence_idx < first_token_idx


def test_evidence_carries_real_document_title(authed_client: TestClient) -> None:
    """The `document_title` in the evidence event must be the chunk's real
    document title (from metadata), falling back to the document_id only
    when the title is absent."""
    import json as _json

    # Chunk with a real title in metadata.
    chunk = _fake_chunk()
    chunk = chunk.model_copy(update={"metadata": {"title": "Remote Work Policy"}})
    rc = RankedChunk(chunk=chunk, score=0.9, rank=1, retriever="rrf")
    events: list[Any] = [
        EvidenceEvent(evidence=[rc]),
        DoneEvent(
            response=FinalResponse(
                answer="The policy allows remote work.",
                evidence=[rc],
                citations=[1],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "remote work?"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())

    # Collect all evidence data lines.
    evidence_payloads = []
    for i, ln in enumerate(lines):
        if ln.startswith("event: evidence"):
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("data:"):
                    evidence_payloads.append(_json.loads(lines[j][len("data:") :].strip()))
                    break

    assert len(evidence_payloads) == 1
    assert evidence_payloads[0]["document_title"] == "Remote Work Policy"

    # Fallback: a chunk without a title in metadata uses the document_id.
    chunk2 = _fake_chunk("HR-099:v1:0001")
    rc2 = RankedChunk(chunk=chunk2, score=0.7, rank=1, retriever="rrf")
    events2: list[Any] = [
        EvidenceEvent(evidence=[rc2]),
        DoneEvent(
            response=FinalResponse(
                answer="fallback",
                evidence=[rc2],
                citations=[1],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events2)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "fallback?"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())

    for i, ln in enumerate(lines):
        if ln.startswith("event: evidence"):
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("data:"):
                    payload = _json.loads(lines[j][len("data:") :].strip())
                    assert payload["document_title"] == "HR-099"
                    break


def test_citation_ranks_are_valid_against_evidence(authed_client: TestClient) -> None:
    rc1 = RankedChunk(chunk=_fake_chunk("HR-002:v1:0001"), score=0.9, rank=1, retriever="rrf")
    rc2 = RankedChunk(chunk=_fake_chunk("HR-003:v1:0001"), score=0.8, rank=2, retriever="rrf")
    events: list[Any] = [
        EvidenceEvent(evidence=[rc1, rc2]),
        TokenEvent(text="See [1] and [2]."),
        DoneEvent(
            response=FinalResponse(
                answer="See [1] and [2].",
                evidence=[rc1, rc2],
                citations=[1, 2],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    import json as _json

    done_payload: dict[str, Any] = {}
    with authed_client.stream("POST", "/api/chat", json={"query": "x"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())
        # Locate the done event's data line.
        for i, ln in enumerate(lines):
            if ln.startswith("event: done"):
                # The data line should follow.
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("data:"):
                        done_payload = _json.loads(lines[j][len("data:") :].strip())
                        break
                break

    assert done_payload["citations"] == [1, 2]
    assert len(done_payload["evidence"]) == 2
    assert all(1 <= c <= len(done_payload["evidence"]) for c in done_payload["citations"])


def test_l1_cache_hit_emits_only_done_with_no_evidence(authed_client: TestClient) -> None:
    # Stub the assistant to emit a single done event with no evidence (cache-hit shape).
    events: list[Any] = [
        DoneEvent(
            response=FinalResponse(
                answer="cached answer",
                evidence=[],
                citations=[],
                model="cache",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "anything"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())
        event_types = [ln[len("event:") :].strip() for ln in lines if ln.startswith("event:")]
        assert event_types == ["done"]
        # The done event must carry the documented MVP caveat.
        import json as _json

        data_line = next(ln[len("data:") :].strip() for ln in lines if ln.startswith("data:"))
        payload = _json.loads(data_line)
        assert payload["answer"] == "cached answer"
        assert payload["citations"] == []
        assert payload["evidence"] == []
        assert payload["extras"].get("note") == CACHE_HIT_NOTE


def test_refuse_route_emits_done_with_no_evidence(authed_client: TestClient) -> None:
    events: list[Any] = [
        DoneEvent(
            response=FinalResponse(
                answer="I am sorry, but I cannot answer that question as it is outside my scope.",
                evidence=[],
                citations=[],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "asdf"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())
        event_types = [ln[len("event:") :].strip() for ln in lines if ln.startswith("event:")]
        assert event_types == ["done"]


def test_meta_event_is_emitted_first_with_route_and_cache_tier(
    authed_client: TestClient,
) -> None:
    """The ``meta`` event must arrive before evidence/token/done and carry
    the route + cache_tier the pipeline visualization consumes."""
    import json as _json

    chunk = _fake_chunk()
    rc = RankedChunk(chunk=chunk, score=0.9, rank=1, retriever="rrf")
    events: list[Any] = [
        MetaEvent(route="DOCUMENT_RAG", cache_tier="MISS"),
        EvidenceEvent(evidence=[rc]),
        TokenEvent(text="Answer."),
        DoneEvent(
            response=FinalResponse(
                answer="Answer.",
                evidence=[rc],
                citations=[1],
                model="llama3",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "remote work?"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())

    order = [ln[len("event:") :].strip() for ln in lines if ln.startswith("event:")]
    # meta is first, and precedes evidence/token/done.
    assert order[0] == "meta"
    assert order.index("meta") < order.index("evidence")
    assert order.index("evidence") < order.index("token") < order.index("done")

    # The meta data line carries the route + cache_tier verbatim.
    meta_idx = next(i for i, ln in enumerate(lines) if ln.startswith("event: meta"))
    meta_data = next(
        lines[j][len("data:") :].strip()
        for j in range(meta_idx + 1, len(lines))
        if lines[j].startswith("data:")
    )
    payload = _json.loads(meta_data)
    assert payload["route"] == "DOCUMENT_RAG"
    assert payload["cache_tier"] == "MISS"


def test_meta_event_on_cache_hit_has_null_route(authed_client: TestClient) -> None:
    """On a cache hit the router is skipped, so ``route`` is null but the
    cache tier is still reported."""
    import json as _json

    events: list[Any] = [
        MetaEvent(route=None, cache_tier="L1"),
        DoneEvent(
            response=FinalResponse(
                answer="cached answer",
                evidence=[],
                citations=[],
                model="cache",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )
        ),
    ]
    authed_client.app.state.assistant = _StubAssistant(events)  # type: ignore[assignment]

    with authed_client.stream("POST", "/api/chat", json={"query": "anything"}) as r:
        assert r.status_code == 200
        lines = list(r.iter_lines())

    order = [ln[len("event:") :].strip() for ln in lines if ln.startswith("event:")]
    assert order == ["meta", "done"]

    meta_data = next(ln[len("data:") :].strip() for ln in lines if ln.startswith("data:"))
    payload = _json.loads(meta_data)
    assert payload["route"] is None
    assert payload["cache_tier"] == "L1"
