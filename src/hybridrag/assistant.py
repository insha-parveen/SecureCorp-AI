"""High-level orchestration for the SecureCorp AI Assistant.

This module ties together caching, routing, structured retrieval, hybrid RAG retrieval,
and generation into a single request-response flow.
"""

from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.caching.redis_cache import RedisCache
from hybridrag.config import Settings, get_settings
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import get_generation_provider
from hybridrag.indexing.embeddings import get_embedding_provider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.routing.router import QueryRouter, Route
from hybridrag.structured.db import DatabaseManager
from hybridrag.structured.query_path import StructuredQueryPath


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

        # Structured Path
        self._db = DatabaseManager(self._settings)
        self._sql_path = StructuredQueryPath(self._db)

        # RAG Path
        self._retriever: HybridRetriever | None = None  # Lazy loaded or passed in
        self._generator = RAGGenerator(self._provider, self._settings)

    def set_retriever(self, retriever: HybridRetriever) -> None:
        self._retriever = retriever

    def ask(self, query: str, user_context: UserContext) -> str:
        """Handle a user query from caching to final answer."""

        # 1. Try L1 Exact Cache
        cached_exact = self._cache.get_exact(query, user_context)
        if cached_exact:
            return cached_exact

        # 2. Try L2 Semantic Cache
        query_embedding = self._embeddings.embed_query(query)
        cached_semantic = self._cache.get_semantic(query_embedding, query, user_context)
        if cached_semantic:
            return cached_semantic

        # 3. Route the query
        route = self._router.route(query)

        if route == Route.REFUSE:
            return "I am sorry, but I cannot answer that question as it is outside my scope."

        answer = ""
        if route == Route.STRUCTURED_SQL:
            # 3a. Structured Path
            result = self._sql_path.query(query, user_context)
            if "error" in result:
                return str(result["error"])

            # We wrap the structured result as 'evidence' for the generator
            answer = self._generate_from_structured(query, result)

        elif route == Route.DOCUMENT_RAG:
            # 3b. RAG Path
            if not self._retriever:
                return "Retrieval system is not initialized."

            evidence = self._retriever.retrieve(query, user_context=user_context)
            response = self._generator.generate_answer(query, evidence)
            answer = response.answer

        if not answer:
            return "I'm not sure how to handle this request."

        # 4. Store in Cache
        self._cache.set_exact(query, answer, user_context)
        self._cache.set_semantic(query, query_embedding, answer, user_context)

        return answer

    def _generate_from_structured(self, query: str, result: dict[str, Any]) -> str:
        """Convert structured SQL results into a natural language answer."""
        context = (
            f"Structured Data from table {result['table']}:\n"
            f"{result['data']}\n"
            f"SQL Query: {result['query']}"
        )

        prompt = (
            f"The user asked: {query}\n\n"
            f"I found the following structured data:\n{context}\n\n"
            "Please provide a concise, professional answer based on this data."
        )

        response = self._provider.generate(prompt=prompt)
        return str(response.text)
