"""Embedding provider abstraction and the SentenceTransformer implementation.

Nothing outside this module may import ``sentence_transformers``. Callers
depend on the :class:`EmbeddingProvider` protocol, so a hosted provider (Groq,
OpenAI, Cohere) can be added later without touching the indexing pipeline,
retrieval, or the evaluation harness — the same rule CLAUDE.md §17 applies to
vector stores and LLM providers.

Two design points worth stating explicitly:

* **Documents and queries are embedded through separate methods.** They are
  identical for the symmetric MiniLM baseline, but asymmetric models (``e5-*``,
  ``bge-*``) require different prefixes on each side, and getting that wrong
  silently degrades recall rather than raising. Splitting the methods now means
  swapping models later is a configuration change, not a code change.
* **``model_name`` is part of the provider's public surface.** The indexing
  pipeline records it alongside every vector so a model swap can be detected
  and the affected embeddings recomputed instead of silently mixing vector
  spaces inside one collection.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from hybridrag.config import Settings, get_settings

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids importing torch
    from sentence_transformers import SentenceTransformer


@runtime_checkable
class EmbeddingProvider(Protocol):
    """The contract every embedding backend must satisfy."""

    @property
    def model_name(self) -> str:
        """Identifier of the underlying model, recorded with each vector."""
        ...

    @property
    def dimension(self) -> int:
        """Vector width; used to validate a collection's existing vectors."""
        ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed corpus passages, in the same order as ``texts``."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        ...


class SentenceTransformerEmbeddings:
    """Local ``sentence-transformers`` provider (the default, offline backend).

    The model is loaded lazily on first use: importing this module must stay
    cheap so unit tests, the CLI, and the ingestion path never pay a multi-
    second torch import for a model they will not call.
    """

    def __init__(
        self,
        model_name: str,
        *,
        batch_size: int = 32,
        normalize: bool = True,
        device: str | None = None,
        document_prefix: str = "",
        query_prefix: str = "",
    ) -> None:
        self._model_name = model_name
        self._batch_size = batch_size
        self._normalize = normalize
        self._device = device
        self._document_prefix = document_prefix
        self._query_prefix = query_prefix
        self._model: SentenceTransformer | None = None

    # -- construction ------------------------------------------------------

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "SentenceTransformerEmbeddings":
        """Build a provider from application configuration (never hardcoded)."""
        cfg = settings or get_settings()
        return cls(
            cfg.embedding_model,
            batch_size=cfg.embedding_batch_size,
            normalize=cfg.embedding_normalize,
            device=cfg.embedding_device,
            document_prefix=cfg.embedding_document_prefix,
            query_prefix=cfg.embedding_query_prefix,
        )

    # -- protocol ----------------------------------------------------------

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return int(self._load().get_sentence_embedding_dimension() or 0)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._encode([self._document_prefix + t for t in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._encode([self._query_prefix + text])[0]

    # -- internals ---------------------------------------------------------

    def _load(self) -> "SentenceTransformer":
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name, device=self._device)
        return self._model

    def _encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._load().encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        # Cast away numpy at the boundary: downstream code (Chroma, JSON, the
        # evaluation harness) should never need to know about ndarray types.
        return [[float(value) for value in row] for row in vectors]


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Return the configured embedding provider.

    The single place provider selection happens. When a hosted provider is
    added, this function grows a branch on a config value; every caller stays
    unchanged.
    """
    return SentenceTransformerEmbeddings.from_settings(settings)
