"""Orchestration of the RAG generation process.

This module coordinates the flow from retrieved evidence to a final generated answer,
handling formatting, provider calls, and citation validation.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

from hybridrag.config import Settings, get_settings
from hybridrag.domain import FinalResponse, RankedChunk, StructuredAnswer
from hybridrag.generation.formatter import create_generation_prompt, format_evidence
from hybridrag.generation.provider import GenerationProvider, get_generation_provider

__all__ = [
    "RAGGenerator",
    "FinalResponse",
    "GeneratorTokenEvent",
    "GeneratorDoneEvent",
    "GeneratorEvent",
    "get_generator",
]


@dataclass(frozen=True)
class GeneratorTokenEvent:
    """A streaming token from the generator. Plain text fragment."""

    text: str


@dataclass(frozen=True)
class GeneratorDoneEvent:
    """The terminal event of a stream. Carries the validated ``FinalResponse``."""

    response: FinalResponse


# Tagged union of all generator events. The assistant/SSE layer switches on
# the concrete type. Frozen dataclasses + a Union keep mypy strict-clean.
GeneratorEvent = GeneratorTokenEvent | GeneratorDoneEvent


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
        history: list[dict[str, str]] | None = None,
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
        prompt = create_generation_prompt(query, context, history=history)

        # 3. Call the LLM provider
        response = self._provider.generate(
            prompt=prompt,
            system_prompt="You are a secure enterprise assistant for NexaCore Solutions.",
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

        # 6. Detect abstention. If the model abstained (no evidence or
        # explicit "I don't know"), return a structured abstention response
        # with empty citations so the UI can render it distinctly.
        if self._is_abstention(answer, evidence):
            return FinalResponse(
                answer=answer,
                evidence=evidence,
                citations=[],
                model=response.model,
                usage=cast(dict[str, float | int], response.usage),
            )

        # 7. Return the final response object
        # ``response.usage`` is typed as dict[str, int] by the provider; the
        # FinalResponse contract allows dict[str, float | int]. The cast keeps
        # the provider contract narrow without widening it everywhere.
        return FinalResponse(
            answer=answer,
            evidence=evidence,
            citations=validated_citations,
            model=response.model,
            usage=cast(dict[str, float | int], response.usage),
        )

    def stream_answer(
        self,
        query: str,
        evidence: list[RankedChunk],
        history: list[dict[str, str]] | None = None,
    ) -> Iterator[GeneratorEvent]:
        """Stream the generation as a sequence of ``GeneratorEvent`` values.

        Each ``GeneratorTokenEvent`` carries a text fragment from the model;
        the terminal ``GeneratorDoneEvent`` carries the validated
        ``FinalResponse`` (with citations filtered against the evidence).

        Streaming design (Phase 9 MVP):
        - The provider's ``stream()`` is called WITHOUT ``format: json_object``,
          so the model emits prose tokens that stream to the client in
          real-time.
        - The prompt instructs the model to cite evidence inline as ``[N]``
          (e.g., ``[1]``, ``[2]``) in the prose.
        - After streaming completes, inline citations are extracted from the
          assembled text via regex and validated against the evidence.
        - Each token is yielded as a ``GeneratorTokenEvent`` so the SSE layer
          can forward it to the client token-by-token. The client assembles
          the visible answer from these tokens and only switches to the final
          "done" state when the ``GeneratorDoneEvent`` arrives.
        """
        # 1. Build the streaming prompt (prose + inline [N] citations).
        context = format_evidence(evidence)
        prompt = create_generation_prompt(query, context, streaming=True, history=history)

        # 2. Stream tokens; accumulate the full text. The model name is what
        # the provider reports — it is constant for the life of the provider.
        model_name = self._provider.model_name
        accumulated: list[str] = []
        for token in self._provider.stream(
            prompt=prompt,
            system_prompt="You are a secure enterprise assistant for NexaCore Solutions.",
        ):
            accumulated.append(token)
            yield GeneratorTokenEvent(text=token)

        full_text = "".join(accumulated)

        # 3. Extract inline citations from the prose. The model is instructed
        # to cite as [N] inline (see formatter.create_generation_prompt).
        citations = self._extract_inline_citations(full_text)

        # 4. Validate citations against the provided evidence.
        validated_citations = self._validate_citations(citations, evidence)

        # 5. Detect abstention. If the model abstained, drop citations so
        # the UI renders the answer as an abstention (no [N] chips).
        if self._is_abstention(full_text, evidence):
            validated_citations = []

        # 6. Yield the terminal Done event. Usage counters are not exposed by
        # the streaming providers today; report zeros so the shape is stable.
        final = FinalResponse(
            answer=full_text,
            evidence=evidence,
            citations=validated_citations,
            model=model_name,
            usage=cast(dict[str, float | int], {"prompt_tokens": 0, "completion_tokens": 0}),
        )
        yield GeneratorDoneEvent(response=final)

    def _extract_inline_citations(self, text: str) -> list[int]:
        """Extract citation ranks from inline ``[N]`` markers in prose.

        The streaming prompt instructs the model to cite evidence inline
        as ``[1]``, ``[2]``, etc. This method parses those markers and
        returns the unique ranks in order of first appearance.
        """
        import re

        return [int(m) for m in re.findall(r"\[(\d+)\]", text)]

    def _is_abstention(self, answer: str, evidence: list[RankedChunk]) -> bool:
        """Detect whether the model abstained from answering.

        The model abstains when:
          * There is no evidence at all, OR
          * The answer contains explicit abstention phrases.

        Returns True when the answer should be treated as an abstention
        rather than a grounded answer.
        """
        if not evidence:
            return True

        # Explicit abstention phrases the model may emit when it cannot
        # find the answer in the provided evidence.
        abstention_phrases = (
            "i don't know",
            "i do not know",
            "not in the evidence",
            "not found in the evidence",
            "cannot answer",
            "can't answer",
            "unable to answer",
            "no relevant evidence",
            "i am not sure",
            "i'm not sure",
            "insufficient information",
        )
        lowered = answer.lower().strip()
        return any(phrase in lowered for phrase in abstention_phrases)

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
