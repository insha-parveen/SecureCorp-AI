"""High-level orchestration for the SecureCorp AI Assistant.

This module ties together caching, routing, structured retrieval, hybrid RAG retrieval,
and generation into a single request-response flow.
"""

import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.caching.history import ConversationHistory
from hybridrag.caching.redis_cache import RedisCache
from hybridrag.config import Settings, get_settings
from hybridrag.domain import FinalResponse, RankedChunk
from hybridrag.generation.generator import (
    GeneratorDoneEvent,
    GeneratorTokenEvent,
    RAGGenerator,
)
from hybridrag.generation.provider import get_generation_provider
from hybridrag.indexing.embeddings import get_embedding_provider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.routing.router import QueryRouter, Route
from hybridrag.structured.db import DatabaseManager
from hybridrag.structured.query_path import StructuredQueryPath


@dataclass(frozen=True)
class EvidenceEvent:
    """A list of evidence chunks has been retrieved (and authorized) for a query."""

    evidence: list[RankedChunk]


@dataclass(frozen=True)
class MetaEvent:
    """Pipeline telemetry for the request, emitted before evidence/tokens.

    Carries the two facts the frontend pipeline visualization needs but
    cannot infer from the token/evidence stream:

    - ``route``: the route the query took (``DOCUMENT_RAG`` / ``STRUCTURED_SQL``
      / ``REFUSE``), or ``None`` on a cache hit where the router is genuinely
      skipped (emitting a route there would be inventing data).
    - ``cache_tier``: ``"L1"`` (exact hit), ``"L2"`` (semantic hit), or
      ``"MISS"`` (full path ran).

    This is additive telemetry only: both values are already computed and
    already logged to ``query_logs``; the event changes no routing,
    retrieval, authorization, generation, or caching behavior.
    """

    route: str | None
    cache_tier: str


@dataclass(frozen=True)
class TokenEvent:
    """An incremental text token from the generation path."""

    text: str


@dataclass(frozen=True)
class DoneEvent:
    """The terminal event: a complete ``FinalResponse`` for the query."""

    response: FinalResponse


# Tagged union: the SSE layer dispatches on concrete type.
AssistantEvent = MetaEvent | EvidenceEvent | TokenEvent | DoneEvent


class SecureCorpAssistant:
    """The main entry point for the SecureCorp AI system."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        # Providers
        self._provider = get_generation_provider(self._settings)
        self._embeddings = get_embedding_provider(self._settings)

        # Components
        self._router = QueryRouter(self._provider, self._settings)
        self._cache = RedisCache(self._settings)
        self._history = ConversationHistory(self._settings)

        # Structured Path
        self._db = DatabaseManager(self._settings)
        self._sql_path = StructuredQueryPath(self._db)

        # RAG Path
        self._retriever: HybridRetriever | None = None  # Lazy loaded or passed in
        self._generator = RAGGenerator(self._provider, self._settings)

    def set_retriever(self, retriever: HybridRetriever) -> None:
        self._retriever = retriever

    def ask(self, query: str, user_context: UserContext, session_id: str | None = None) -> str:
        """Handle a user query from caching to final answer.

        Args:
            query: The user's prompt.
            user_context: Security context for retrieval and caching.
            session_id: Optional ID for maintaining conversation history.
        """
        start_time = time.perf_counter()
        query_id = str(uuid.uuid4())
        cache_hit = "MISS"

        # 1. Try L1 Exact Cache
        cached_exact = self._cache.get_exact(query, user_context)
        if cached_exact:
            answer = cached_exact.answer
            cache_hit = "L1"
            if session_id:
                self._history.add_message(
                    user_context.tenant_id, user_context.user_id, session_id, query, answer
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "DOCUMENT_RAG",
                latency,
                cache_hit,
                latency,
            )
            return answer

        # 2. Try L2 Semantic Cache
        query_embedding = self._embeddings.embed_query(query)
        cached_semantic = self._cache.get_semantic(query_embedding, query, user_context)
        if cached_semantic:
            answer = cached_semantic.answer
            cache_hit = "L2"
            if session_id:
                self._history.add_message(
                    user_context.tenant_id, user_context.user_id, session_id, query, answer
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "DOCUMENT_RAG",
                latency,
                cache_hit,
                latency,
            )
            return answer

        # 3. Route the query
        route = self._router.route(query)

        if route == Route.REFUSE:
            answer = "I am sorry, but I cannot answer that question as it is outside my scope."
            if session_id:
                self._history.add_message(
                    user_context.tenant_id, user_context.user_id, session_id, query, answer
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "REFUSE",
                latency,
                cache_hit,
                latency,
            )
            return answer

        # Retrieve history if provided
        history = None
        if session_id:
            history = self._history.get_history(
                user_context.tenant_id, user_context.user_id, session_id
            )

        answer = ""
        final_response: FinalResponse | None = None
        if route == Route.STRUCTURED_SQL:
            # 3a. Structured Path
            result = self._sql_path.query(query, user_context)
            if "error" in result:
                return str(result["error"])

            # We wrap the structured result as 'evidence' for the generator
            answer = self._generate_from_structured(query, result)
            final_response = self._build_prose_response(answer, user_context)

        elif route == Route.DOCUMENT_RAG:
            # 3b. RAG Path
            if not self._retriever:
                return "Retrieval system is not initialized."

            evidence = self._retriever.retrieve(query, user_context=user_context)
            response = self._generator.generate_answer(query, evidence, history=history)
            answer = response.answer
            final_response = response

        if not answer:
            return "I'm not sure how to handle this request."

        # 4. Store in Cache
        if final_response:
            self._cache.set_exact(query, final_response, user_context)
            self._cache.set_semantic(query, query_embedding, final_response, user_context)

        # 5. Store in History
        if session_id:
            self._history.add_message(
                user_context.tenant_id, user_context.user_id, session_id, query, answer
            )

        # 6. Log to DB
        latency = int((time.perf_counter() - start_time) * 1000)
        self._db.log_query(
            query_id,
            user_context.tenant_id,
            user_context.user_id,
            query,
            route.value,
            latency,
            cache_hit,
            latency,
        )

        return answer

    def ask_stream(
        self, query: str, user_context: UserContext, session_id: str | None = None
    ) -> Iterator[AssistantEvent]:
        """Streaming sibling of :meth:`ask`.

        Yields a sequence of :class:`AssistantEvent` values:

        - ``EvidenceEvent`` (zero or one): the retrieved evidence list. Emitted
          BEFORE the first token, so the SSE layer can populate the sources
          panel instantly.
        - ``TokenEvent`` (zero or more): incremental text fragments from the
          generation path. Each token is a real LLM emission — never faked.
        - ``DoneEvent`` (exactly one, last): the validated ``FinalResponse``.

        Cache behaviour:
        - L1/L2 cache HIT: emits zero ``TokenEvent``s and a single ``DoneEvent``
          with the cached response.
        - L1/L2 cache MISS: emits ``EvidenceEvent`` then ``TokenEvent``s then
          ``DoneEvent``. The final response is written back to L1+L2.

        The structured-SQL path does not stream; its "answer" is a short
        non-LLM prose string. The path emits zero ``TokenEvent``s and a single
        ``DoneEvent`` whose ``FinalResponse.answer`` is the prose answer.
        """
        start_time = time.perf_counter()
        query_id = str(uuid.uuid4())
        cache_hit = "MISS"

        # 1. L1 exact cache
        cached_exact = self._cache.get_exact(query, user_context)
        if cached_exact:
            if session_id:
                self._history.add_message(
                    user_context.tenant_id,
                    user_context.user_id,
                    session_id,
                    query,
                    cached_exact.answer,
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "DOCUMENT_RAG",
                latency,
                "L1",
                latency,
            )
            # Evidence-in-cache: the cached FinalResponse carries its own
            # evidence and citations, so we can re-populate the sources panel.
            yield MetaEvent(route=None, cache_tier="L1")
            if cached_exact.evidence:
                yield EvidenceEvent(evidence=cached_exact.evidence)
            yield DoneEvent(response=cached_exact)
            return

        # 2. L2 semantic cache (compute the query embedding once if we miss)
        query_embedding = self._embeddings.embed_query(query)
        cached_semantic = self._cache.get_semantic(query_embedding, query, user_context)
        if cached_semantic:
            if session_id:
                self._history.add_message(
                    user_context.tenant_id,
                    user_context.user_id,
                    session_id,
                    query,
                    cached_semantic.answer,
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "DOCUMENT_RAG",
                latency,
                "L2",
                latency,
            )
            yield MetaEvent(route=None, cache_tier="L2")
            if cached_semantic.evidence:
                yield EvidenceEvent(evidence=cached_semantic.evidence)
            yield DoneEvent(response=cached_semantic)
            return

        # 3. Route
        route = self._router.route(query)

        # Emit pipeline telemetry once, before any branch produces output.
        # cache_tier is MISS here: we only reach routing on a full cache miss.
        yield MetaEvent(route=route.value, cache_tier="MISS")

        if route == Route.REFUSE:
            answer = "I am sorry, but I cannot answer that question as it is outside my scope."
            if session_id:
                self._history.add_message(
                    user_context.tenant_id, user_context.user_id, session_id, query, answer
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "REFUSE",
                latency,
                "MISS",
                latency,
            )
            yield DoneEvent(
                response=self._build_prose_response(
                    answer,
                    user_context,
                )
            )
            return

        if route == Route.STRUCTURED_SQL:
            result = self._sql_path.query(query, user_context)
            if "error" in result:
                answer = str(result["error"])
            else:
                answer = self._generate_from_structured(query, result)

            if session_id:
                self._history.add_message(
                    user_context.tenant_id, user_context.user_id, session_id, query, answer
                )
            latency = int((time.perf_counter() - start_time) * 1000)
            self._db.log_query(
                query_id,
                user_context.tenant_id,
                user_context.user_id,
                query,
                "STRUCTURED_SQL",
                latency,
                "MISS",
                latency,
            )
            yield DoneEvent(response=self._build_prose_response(answer, user_context))
            return

        # 4. DOCUMENT_RAG
        if not self._retriever:
            yield DoneEvent(
                response=self._build_prose_response(
                    "Retrieval system is not initialized.",
                    user_context,
                )
            )
            return

        # Retrieve history if provided
        history = None
        if session_id:
            history = self._history.get_history(
                user_context.tenant_id, user_context.user_id, session_id
            )

        evidence = self._retriever.retrieve(query, user_context=user_context)
        yield EvidenceEvent(evidence=evidence)

        final_response: FinalResponse | None = None
        for ev in self._generator.stream_answer(query, evidence, history=history):
            assert isinstance(ev, (GeneratorTokenEvent, GeneratorDoneEvent))
            if isinstance(ev, GeneratorTokenEvent):
                yield TokenEvent(text=ev.text)
            else:
                final_response = ev.response
                yield DoneEvent(response=ev.response)

        # 5. Write back to cache.
        if final_response is not None and final_response.answer:
            self._cache.set_exact(query, final_response, user_context)
            self._cache.set_semantic(query, query_embedding, final_response, user_context)

            if session_id:
                self._history.add_message(
                    user_context.tenant_id,
                    user_context.user_id,
                    session_id,
                    query,
                    final_response.answer,
                )

        # 6. Log to DB
        latency = int((time.perf_counter() - start_time) * 1000)
        self._db.log_query(
            query_id,
            user_context.tenant_id,
            user_context.user_id,
            query,
            "DOCUMENT_RAG",
            latency,
            cache_hit,
            latency,
        )

    # -- helpers ----------------------------------------------------------

    def _build_prose_response(self, answer: str, user_context: UserContext) -> FinalResponse:
        """Build a ``FinalResponse`` from a short prose answer (no evidence).

        Used by the REFUSE and structured-SQL paths where there is no
        retrieval evidence to attach.
        """
        return FinalResponse(
            answer=answer,
            evidence=[],
            citations=[],
            model=self._provider.model_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    def _generate_from_structured(self, query: str, result: dict[str, Any]) -> str:
        """Convert structured SQL results into a natural language answer."""
        context = (
            f"Structured Data from table {result['table']}:\n"
            f"{result['data']}\n"
            f"SQL Query: {result['query']}"
        )

        # The structured-SQL answer is short prose that names the
        # number or record the user asked for. We pass json_mode=False
        # so the provider does not wrap the answer in a JSON envelope
        # (which Groq enforces when json_mode=True and which makes the
        # prose unreadable in the UI).
        system_prompt = (
            "You are an enterprise assistant. Answer in plain prose based "
            "on the structured data provided. Be concise and professional."
        )

        prompt = (
            f"The user asked: {query}\n\n"
            f"I found the following structured data:\n{context}\n\n"
            "Please provide a concise, professional answer based on this data."
        )

        response = self._provider.generate(
            prompt=prompt, system_prompt=system_prompt, json_mode=False
        )
        return str(response.text)
