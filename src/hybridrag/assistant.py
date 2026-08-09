"""High-level orchestration for the SecureCorp AI Assistant.

This module ties together routing, structured retrieval, hybrid RAG retrieval,
and generation into a single request-response flow.
"""

from typing import Any
from hybridrag.config import Settings, get_settings
from hybridrag.authorization.models import UserContext
from hybridrag.routing.router import QueryRouter, Route
from hybridrag.structured.query_path import StructuredQueryPath
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.generation.generator import RAGGenerator
from hybridrag.structured.db import DatabaseManager
from hybridrag.generation.provider import get_generation_provider

class SecureCorpAssistant:
    """The main entry point for the SecureCorp AI system."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        # Components
        self._provider = get_generation_provider(self._settings)
        self._router = QueryRouter(self._provider, self._settings)

        # Structured Path
        self._db = DatabaseManager(self._settings)
        self._sql_path = StructuredQueryPath(self._db)

        # RAG Path (Assuming components are provided or created)
        # For simplicity in this orchestration, we assume the retriever is setup
        # In a real app, we'd pass these in or use a factory.
        self._retriever = None # Lazy loaded or passed in
        self._generator = RAGGenerator(self._provider, self._settings)

    def set_retriever(self, retriever: HybridRetriever) -> None:
        self._retriever = retriever

    def ask(self, query: str, user_context: UserContext) -> str:
        """Handle a user query from routing to final answer."""

        # 1. Route the query
        route = self._router.route(query)

        if route == Route.REFUSE:
            return "I am sorry, but I cannot answer that question as it is outside my scope."

        if route == Route.STRUCTURED_SQL:
            # 2a. Structured Path
            result = self._sql_path.query(query, user_context)
            if "error" in result:
                return result["error"]

            # We wrap the structured result as 'evidence' for the generator
            # The generator needs to be updated to handle this.
            return self._generate_from_structured(query, result)

        if route == Route.DOCUMENT_RAG:
            # 2b. RAG Path
            if not self._retriever:
                return "Retrieval system is not initialized."

            evidence = self._retriever.retrieve(query, user_context=user_context)
            response = self._generator.generate_answer(query, evidence)
            return response.answer

        return "I'm not sure how to handle this request."

    def _generate_from_structured(self, query: str, result: dict[str, Any]) -> str:
        """Convert structured SQL results into a natural language answer.

        This is a simplified flow that uses the LLM to summarize the table data.
        """
        context = f"Structured Data from table {result['table']}:\n{result['data']}\nSQL Query: {result['query']}"

        # We use the provider directly for a simple summary
        prompt = (
            f"The user asked: {query}\n\n"
            f"I found the following structured data:\n{context}\n\n"
            "Please provide a concise, professional answer based on this data."
        )

        response = self._provider.generate(prompt=prompt)
        return response.text
