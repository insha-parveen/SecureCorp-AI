"""Orchestration of the RAG generation process.

This module coordinates the flow from retrieved evidence to a final generated answer,
handling formatting, provider calls, and citation validation.
"""

import json
from typing import Any

from hybridrag.config import Settings, get_settings
from hybridrag.domain import RankedChunk, StructuredAnswer, FinalResponse
from hybridrag.generation.formatter import create_generation_prompt, format_evidence
from hybridrag.generation.provider import GenerationProvider, GenerationResponse, get_generation_provider


class RAGGenerator:
    """Coordinate the transition from retrieval to generation."""

    def __init__(
        self,
        provider: GenerationProvider,
        settings: Settings | None = None,
    ) -> None:
        self._provider = provider
        self._settings = settings or get_settings()

    def generate_answer(
        self,
        query: str,
        evidence: list[RankedChunk],
    ) -> FinalResponse:
        """Turn a query and retrieved evidence into a cited answer.

        This method coordinates:
        1. Evidence formatting and prompt construction.
        2. LLM generation (structured JSON).
        3. JSON parsing with graceful fallback.
        4. Citation validation against the provided evidence.
        """
        # 1. Format the evidence for the LLM
        context = format_evidence(evidence)

        # 2. Construct the full prompt
        prompt = create_generation_prompt(query, context)

        # 3. Call the LLM provider
        response = self._provider.generate(
            prompt=prompt,
            system_prompt="You are a secure enterprise assistant for NexaCore Solutions."
        )

        # 4. Parse structured output
        try:
            # Attempt to parse as JSON into the StructuredAnswer model
            structured = StructuredAnswer.model_validate_json(response.text)
            answer = structured.answer
            citations = structured.citations
        except Exception:
            # Fallback: Treat raw text as answer and provide no citations
            answer = response.text
            citations = []

        # 5. Validate citations
        validated_citations = self._validate_citations(citations, evidence)

        # 6. Return the final response object
        return FinalResponse(
            answer=answer,
            evidence=evidence,
            citations=validated_citations,
            model=response.model,
            usage=response.usage
        )

    def _validate_citations(
        self,
        citations: list[int],
        evidence: list[RankedChunk],
    ) -> list[int]:
        """Filter out citations that do not correspond to provided evidence.

        A citation is valid if its rank is between 1 and the total number of
        evidence chunks provided.
        """
        if not evidence:
            return []

        valid_ranks = set(range(1, len(evidence) + 1))
        return [rank for rank in citations if rank in valid_ranks]


def get_generator(settings: Settings | None = None) -> RAGGenerator:
    """Factory to get the configured generator."""
    cfg = settings or get_settings()
    provider = get_generation_provider(cfg)
    return RAGGenerator(provider, settings=cfg)
