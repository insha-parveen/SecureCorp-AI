"""Reciprocal Rank Fusion (RRF) over multiple ranked result lists.

RRF merges ranked lists that share a common item space by adding a score of
``1 / (k + rank)`` for every occurrence of an item, summed across all lists.
Only the *rank order* matters — BM25 scores and dense distances are
incommensurable, so RRF never reads them.

Two properties that follow from the architecture (CLAUDE.md §5, §7):

* **The item space is ``chunk_id``.** Multiple chunks may belong to the same
  document, so fusing on ``document_id`` would collapse distinct evidence into
  one bucket. :class:`~hybridrag.domain.RankedChunk` exposes ``chunk_id``
  precisely so fusion here and citations downstream agree on what a result is.
* **The fused ranks are recomputed, not averaged.** RRF returns a *merged
  ordering*, not a blend of original scores. Callers can then truncate to a
  bounded candidate set before a cross-encoder reranker, whose cost scales with
  the number of pairs it scores.
"""

from collections.abc import Sequence

from hybridrag.config import Settings, get_settings
from hybridrag.domain import RankedChunk

RETRIEVER_NAME = "rrf"


def rrf_fuse(
    *rankings: Sequence[RankedChunk],
    k: int | None = None,
    settings: Settings | None = None,
) -> list[RankedChunk]:
    """Merge several ranked ``RankedChunk`` lists into a single fused ranking.

    Each ``chunk_id`` receives ``sum(1 / (k + rank))`` across every list it
    appears in. Results are returned best-first with fresh 1-based ranks and
    ``retriever="rrf"``, so downstream reranking can take a bounded slice
    without re-deriving rank order.

    Args:
        *rankings: Ranked result lists (typically BM25 then dense) whose
            ``rank`` fields are 1-based within their own list.
        k: The RRF constant. Defaults to ``Settings.rrf_k``. Must be positive.
        settings: Override the application configuration (mostly for tests).

    Raises:
        ValueError: If ``k`` resolves to a non-positive value, which would make
            the ``1 / (k + rank)`` weights meaningless.
    """
    config = settings or get_settings()
    k_value = config.rrf_k if k is None else k
    if k_value <= 0:
        raise ValueError(f"rrf k must be a positive integer, got {k_value}")

    fused: dict[str, float] = {}
    best: dict[str, RankedChunk] = {}
    for ranking in rankings:
        for item in ranking:
            fused[item.chunk_id] = fused.get(item.chunk_id, 0.0) + 1.0 / (k_value + item.rank)
            # Keep the first chunk object seen so every fused result carries
            # full authorization/provenance metadata, losslessly.
            if item.chunk_id not in best:
                best[item.chunk_id] = item

    # Break ties deterministically on chunk_id rather than insertion order.
    ordered = sorted(fused, key=lambda chunk_id: (-fused[chunk_id], chunk_id))
    return [
        RankedChunk(
            chunk=best[chunk_id].chunk,
            score=fused[chunk_id],
            rank=rank,
            retriever=RETRIEVER_NAME,
        )
        for rank, chunk_id in enumerate(ordered, start=1)
    ]
