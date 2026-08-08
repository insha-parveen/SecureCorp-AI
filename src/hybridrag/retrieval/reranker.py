"""Cross-encoder reranking over a bounded candidate set.

Dense and BM25 scores are not comparable across retrievers, and RRF deliberately
discards their magnitudes — so the fused list is in a *plausible* order, not a
*calibrated* one. A cross-encoder scores every candidate against the query
directly, which is the strongest signal available, at the cost of a forward pass
per (query, chunk) pair. That is why this module reranks only a bounded slice —
``rerank_candidates`` — and returns only ``final_top_k`` (CLAUDE.md §7).

Mirrors the pattern established by :mod:`hybridrag.indexing.embeddings`:

- a small :class:`Reranker` protocol keeps every caller decoupled from
  sentence-transformers (a hosted reranker can be added later without touching
  the retrieval pipeline);
- the CrossEncoder is loaded lazily on first use, so unit tests, the CLI, and
  callers that only build candidates never pay a multi-second model load.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from hybridrag.config import Settings, get_settings
from hybridrag.domain import RankedChunk

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids importing torch
    from sentence_transformers import CrossEncoder

RETRIEVER_NAME = "cross_encoder"


@runtime_checkable
class Reranker(Protocol):
    """The contract every reranker backend must satisfy."""

    @property
    def model_name(self) -> str:
        """Identifier of the underlying model, recorded for evaluation."""
        ...

    def rerank(self, query: str, candidates: Sequence[RankedChunk]) -> list[RankedChunk]:
        """Return ``candidates`` reordered (best first) by query relevance.

        Callers are responsible for bounding ``candidates`` and taking the
        desired slice of the result.
        """
        ...


class CrossEncoderReranker:
    """Local sentence-transformers cross-encoder implementation."""

    def __init__(
        self,
        model_name: str,
        *,
        device: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._model: CrossEncoder | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "CrossEncoderReranker":
        """Build from application configuration (never hardcoded)."""
        cfg = settings or get_settings()
        return cls(cfg.reranker_model, device=cfg.embedding_device)

    # -- Reranker ----------------------------------------------------------

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(self, query: str, candidates: Sequence[RankedChunk]) -> list[RankedChunk]:
        if not candidates:
            return []
        scores = self._load().predict([(query, c.chunk.text) for c in candidates])
        ordered = sorted(
            enumerate(candidates), key=lambda pair: (-float(scores[pair[0]]), pair[1].chunk_id)
        )
        return [
            RankedChunk(
                chunk=candidate.chunk,
                score=float(scores[index]),
                rank=rank,
                retriever=RETRIEVER_NAME,
            )
            for rank, (index, candidate) in enumerate(ordered, start=1)
        ]

    # -- internals ---------------------------------------------------------

    def _load(self) -> "CrossEncoder":
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name, device=self._device)
        return self._model


def rerank_top(
    query: str,
    candidates: Sequence[RankedChunk],
    *,
    reranker: Reranker,
    rerank_candidates: int,
    final_top_k: int,
) -> list[RankedChunk]:
    """Rerank at most ``rerank_candidates`` and return the ``final_top_k``.

    A convenience that bounds the candidate slice and trims the reranked output
    so an orchestrator does not duplicate this cut logic. ``final_top_k <= 0``
    yields an empty list; ``rerank_candidates <= 0`` likewise short-circuits to
    an empty result because there is nothing to rerank.
    """
    if final_top_k <= 0 or rerank_candidates <= 0:
        return []
    bounded = list(candidates)[:rerank_candidates]
    reranked = reranker.rerank(query, bounded)
    return reranked[:final_top_k]
