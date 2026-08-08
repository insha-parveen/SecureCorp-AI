"""The provider-agnostic vector-store interface.

CLAUDE.md §23 is explicit: "The core application should depend on a vector-store
interface, not directly on the ChromaDB SDK." This module is that interface.
``chroma_store.py`` is one implementation; a Pinecone or Qdrant adapter can be
added later without the indexing pipeline or retrieval layer changing.

The interface is deliberately small — only the operations the pipeline and
dense retrieval actually need. Anything richer would leak Chroma semantics into
the contract and defeat the point.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class VectorRecord:
    """One stored vector: its id, text payload, flat metadata, and embedding."""

    id: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class VectorMatch:
    """A similarity-search hit.

    ``distance`` is the store's native distance (smaller is closer). Converting
    it to a comparable score is the retrieval layer's job, not the store's —
    different backends use different metrics.
    """

    id: str
    text: str
    metadata: dict[str, Any]
    distance: float


@runtime_checkable
class VectorStore(Protocol):
    """Operations the application requires of any dense index."""

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """Insert or replace records by id."""
        ...

    def delete(self, ids: Sequence[str]) -> None:
        """Delete records by id (no error when an id is absent)."""
        ...

    def get_metadata(self, ids: Sequence[str] | None = None) -> dict[str, dict[str, Any]]:
        """Return stored metadata keyed by id, without fetching embeddings.

        Incremental indexing depends on this being cheap: it is how the
        pipeline learns what is already indexed and at which fingerprint.
        """
        ...

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Similarity search, optionally constrained by a metadata filter."""
        ...

    def count(self) -> int:
        """Number of stored records."""
        ...

    def health(self) -> dict[str, Any]:
        """Backend/collection diagnostics for debugging and CI smoke tests."""
        ...
