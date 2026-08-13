"""Query classification router for the HybridRAG pipeline.

This module decides whether a user query should be handled by the
unstructured document retrieval path (RAG) or the structured SQL path.

Improvements over the original implementation:

  * **Deterministic pre-classifier.** Before calling the LLM, a
    keyword/regex-based classifier checks for obvious structured
    queries (invoice IDs, employee IDs, ticket IDs, counts, sums).
    This provides a fast-path for common structured queries and a
    reliable fallback when the LLM call fails.
  * **LLM as the primary classifier.** The LLM still handles the
    ambiguous cases and the REFUSE route.
"""

import re
from enum import StrEnum

from hybridrag.config import Settings, get_settings
from hybridrag.generation.provider import GenerationProvider


class Route(StrEnum):
    DOCUMENT_RAG = "DOCUMENT_RAG"
    STRUCTURED_SQL = "STRUCTURED_SQL"
    REFUSE = "REFUSE"


# Deterministic patterns that strongly indicate a structured query.
# These are checked BEFORE the LLM call so common structured queries
# get a fast, reliable route without burning an LLM call.
_STRUCTURED_PATTERNS = (
    # Invoice IDs: INV-2026-0108, INV-1001, etc.
    re.compile(r"\binv(?:-\w+)?-\d+\b", re.IGNORECASE),
    # Employee IDs: EMP-0104, EMP-NEX-100, etc.
    re.compile(r"\bemp(?:-\w+)?-\d+\b", re.IGNORECASE),
    # Ticket IDs: INC-1042, TKT-123, etc.
    re.compile(r"\b(?:inc|tkt|ticket)(?:-\w+)?-\d+\b", re.IGNORECASE),
    # Expense claim IDs: EXP-123, CLM-123, etc.
    re.compile(r"\b(?:exp|clm|claim)(?:-\w+)?-\d+\b", re.IGNORECASE),
    # Purchase order IDs: PO-8491, etc.
    re.compile(r"\bpo(?:-\w+)?-\d+\b", re.IGNORECASE),
)

# Keywords that strongly indicate a structured query.
_STRUCTURED_KEYWORDS = (
    "invoice",
    "invoices",
    "employee",
    "employees",
    "headcount",
    "ticket",
    "tickets",
    "expense",
    "expenses",
    "claim",
    "claims",
    "how many",
    "count of",
    "total of",
    "sum of",
    "average of",
    "per department",
    "by department",
    "vendor",
    "vendors",
    "salary",
    "salaries",
    "payroll",
)

# Keywords that indicate a document/RAG query.
_RAG_KEYWORDS = (
    "policy",
    "policies",
    "handbook",
    "guideline",
    "guidelines",
    "procedure",
    "procedures",
    "sop",
    "how to",
    "what is the",
    "what are the",
    "tell me about",
    "explain",
    "remote work",
    "leave",
    "password",
    "security",
    "onboarding",
    "offboarding",
    "benefits",
    "vacation",
    "sick",
    "maternity",
    "paternity",
    "code of conduct",
    "ethics",
    "travel",
    "reimbursement",
    "expense policy",
    "it policy",
    "hr policy",
    "finance policy",
)


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
        # 0. Deterministic pre-classifier — fast path for obvious
        # structured queries and a reliable fallback if the LLM fails.
        deterministic = self._deterministic_route(query)
        if deterministic is not None:
            return deterministic

        # The JSON envelope is required because the Groq provider runs
        # with ``response_format: json_object``; that constraint requires
        # the literal word "json" to appear somewhere in the messages or
        # Groq rejects the request. The router prompt itself contains
        # "json" twice (see below), which satisfies the contract whether
        # the model reads the system or the user block.
        system_prompt = (
            "You are a query router for an enterprise assistant. "
            "Classify the user query into exactly one of these categories and "
            "respond as a single JSON line:\n\n"
            "1. DOCUMENT_RAG: Questions about policies, handbooks, general "
            "guidelines, conceptual questions, 'how-to' procedures, or general "
            "company overview. If the user asks 'tell me about the company' or "
            "similar broad questions, use this.\n"
            "2. STRUCTURED_SQL: Questions about specific records (invoices, "
            "employees, tickets), counts, totals, sums, or specific business "
            "data points (e.g., 'how many employees').\n"
            "3. REFUSE: Queries that are out-of-scope, nonsensical, or violate "
            "safety guidelines.\n\n"
            "Return ONLY the JSON object with key 'route' and one of the values "
            "'DOCUMENT_RAG', 'STRUCTURED_SQL', or 'REFUSE'."
        )

        try:
            response = self._provider.generate(
                prompt=f"Query: {query}", system_prompt=system_prompt
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

    def _deterministic_route(self, query: str) -> Route | None:
        """Return a deterministic route for obvious queries, or None.

        This is a fast-path classifier that runs BEFORE the LLM call.
        It catches the most common structured-query patterns so we don't
        spend an LLM call on them, and it provides a reliable fallback
        when the LLM is unavailable.
        """
        lowered = query.lower().strip()

        # 1. Structured ID patterns — the strongest signal.
        for pattern in _STRUCTURED_PATTERNS:
            if pattern.search(query):
                return Route.STRUCTURED_SQL

        # 2. Structured keywords.
        for keyword in _STRUCTURED_KEYWORDS:
            if keyword in lowered:
                return Route.STRUCTURED_SQL

        # 3. RAG keywords — only if no structured keyword matched.
        for keyword in _RAG_KEYWORDS:
            if keyword in lowered:
                return Route.DOCUMENT_RAG

        # 4. No deterministic match — let the LLM decide.
        return None
