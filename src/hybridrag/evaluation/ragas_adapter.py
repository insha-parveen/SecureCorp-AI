"""Adapters that wrap project LLM/embedding providers for RAGAS consumption.

These classes satisfy the duck-typed interface RAGAS expects from its
``llm=`` and ``embeddings=`` arguments. The wrapping is deliberately thin:
no prompts are reformatted, no retries are added, no fallbacks. The
underlying provider is the same one ``/query`` uses, so the metrics reflect
the production path.

Off-path guarantee: this module is imported only by ``scripts/run_ragas.py``
and the orchestrator. It is never imported by ``assistant.py`` or the API
layer — RAGAS is offline evaluation, not a runtime dependency.
"""

from __future__ import annotations

from typing import Any

from hybridrag.generation.provider import GenerationProvider
from hybridrag.indexing.embeddings import EmbeddingProvider


class ProjectRagasLLM:
    """Wrap a ``GenerationProvider`` for RAGAS.

    RAGAS calls ``generate_text(prompt, n=1, ...)`` and expects a list of
    strings back. We delegate to the project's GenerationProvider (Groq or
    Ollama) and return one synthetic completion per requested ``n``.

    The class also exposes ``model_name`` so RAGAS can label its outputs.
    """

    def __init__(self, provider: GenerationProvider) -> None:
        self._provider = provider

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    def generate_text(self, prompt: str, n: int = 1, **kwargs: Any) -> list[str]:
        """Generate ``n`` completions for ``prompt`` via the project provider."""
        response = self._provider.generate(
            prompt=prompt,
            system_prompt=str(kwargs.get("system_prompt")) if kwargs.get("system_prompt") else None,
        )
        return [response.text for _ in range(max(1, n))]

    async def agenerate_text(self, prompt: str, n: int = 1, **kwargs: Any) -> list[str]:
        return self.generate_text(prompt, n=n, **kwargs)

    def is_finished(self, response: list[str]) -> bool:
        """All RAGAS responses from this adapter are finished in one call."""
        return True


class ProjectRagasEmbeddings:
    """Wrap an ``EmbeddingProvider`` for RAGAS.

    RAGAS calls ``embed_query(text)`` and ``embed_documents(texts)`` and
    expects ``list[float]`` and ``list[list[float]]`` back. The project's
    SentenceTransformer provider already returns that shape.
    """

    def __init__(self, embeddings: EmbeddingProvider) -> None:
        self._embeddings = embeddings

    @property
    def model_name(self) -> str:
        return self._embeddings.model_name

    def embed_query(self, text: str) -> list[float]:
        return list(self._embeddings.embed_query(text))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(v) for v in self._embeddings.embed_documents(texts)]
