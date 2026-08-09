"""Query classification router for the HybridRAG pipeline.

This module decides whether a user query should be handled by the
unstructured document retrieval path (RAG) or the structured SQL path.
"""

from enum import StrEnum
from hybridrag.config import Settings, get_settings
from hybridrag.generation.provider import GenerationProvider, get_generation_provider

class Route(StrEnum):
    DOCUMENT_RAG = "DOCUMENT_RAG"
    STRUCTURED_SQL = "STRUCTURED_SQL"
    REFUSE = "REFUSE"

class QueryRouter:
    """Classify queries into RAG, SQL, or Refuse paths."""

    def __init__(
        self,
        provider: GenerationProvider,
        settings: Settings | None = None,
    ) -> None:
        self._provider = provider
        self._settings = settings or get_settings()

    def route(self, query: str) -> Route:
        """Classify the query using a fast LLM call.

        Returns a Route enum indicating the target path.
        """
        system_prompt = (
            "You are a query router for an enterprise assistant. "
            "Classify the user query into exactly one of these categories:\n\n"
            "1. DOCUMENT_RAG: Questions about policies, handbooks, general guidelines, "
            "conceptual questions, or 'how-to' procedures.\n"
            "2. STRUCTURED_SQL: Questions about specific records (invoices, employees, tickets), "
            "counts, totals, sums, or specific business data points.\n"
            "3. REFUSE: Queries that are out-of-scope, nonsensical, or violate safety guidelines.\n\n"
            "Return ONLY the category name (e.g., 'STRUCTURED_SQL')."
        )

        try:
            response = self._provider.generate(
                prompt=f"Query: {query}",
                system_prompt=system_prompt
            )
            # Clean the response to match the Route enum
            route_text = response.text.strip().upper()

            for route in Route:
                if route.value in route_text:
                    return route

        except Exception:
            # Fallback to RAG on error
            return Route.DOCUMENT_RAG

        return Route.DOCUMENT_RAG
