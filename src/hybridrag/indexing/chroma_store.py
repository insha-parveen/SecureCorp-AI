"""ChromaDB implementation of :class:`~hybridrag.indexing.vector_store.VectorStore`.

This is the ONLY module allowed to import ``chromadb`` (CLAUDE.md §7, §23).
Everything else depends on the ``VectorStore`` protocol, which is what keeps a
later migration to a hosted vector database a one-file change.

Two decisions worth recording:

* **Embeddings are always supplied by the caller.** The collection is created
  without a Chroma embedding function, so Chroma never silently downloads or
  applies a model of its own. The configured
  :class:`~hybridrag.indexing.embeddings.EmbeddingProvider` is the single
  source of vectors, which is what makes the embedding model configurable and
  the index reproducible.
* **Cosine space.** Set at collection creation via ``hnsw:space``; it matches
  the normalized MiniLM baseline. The metric is fixed for a collection's
  lifetime, so changing it means rebuilding the index.
"""

from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hybridrag.config import Settings, get_settings
from hybridrag.indexing.vector_store import VectorMatch, VectorRecord

if TYPE_CHECKING:  # pragma: no cover - typing only
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection

#: Distance metric for the collection; see the module docstring.
DISTANCE_SPACE = "cosine"


class ChromaVectorStore:
    """Persistent, local-first Chroma collection behind the store interface."""

    def __init__(self, persist_dir: Path, collection_name: str) -> None:
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client: ClientAPI | None = None
        self._collection: Collection | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "ChromaVectorStore":
        cfg = settings or get_settings()
        return cls(cfg.chroma_dir, cfg.chroma_collection)

    # -- lazy connection ---------------------------------------------------

    @property
    def collection(self) -> "Collection":
        """Open the persistent collection on first use.

        Lazy so that importing the indexing package — which the CLI and tests
        do — never creates ``data/chroma_db/`` as a side effect.
        """
        if self._collection is None:
            import chromadb

            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": DISTANCE_SPACE},
                embedding_function=None,  # vectors are always supplied by us
            )
        return self._collection

    # -- VectorStore -------------------------------------------------------

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        self.collection.upsert(
            ids=[r.id for r in records],
            documents=[r.text for r in records],
            metadatas=[r.metadata for r in records],
            embeddings=[r.embedding for r in records],  # type: ignore[arg-type]
        )

    def delete(self, ids: Sequence[str]) -> None:
        if ids:
            self.collection.delete(ids=list(ids))

    def get_metadata(self, ids: Sequence[str] | None = None) -> dict[str, dict[str, Any]]:
        # ``include`` deliberately omits documents and embeddings: the pipeline
        # only needs fingerprints, and pulling vectors for the whole corpus to
        # decide what to skip would defeat incremental indexing.
        result = self.collection.get(
            ids=list(ids) if ids is not None else None,
            include=["metadatas"],
        )
        stored_ids = result.get("ids") or []
        metadatas = result.get("metadatas") or []
        return {
            str(stored_id): dict(meta or {})
            for stored_id, meta in zip(stored_ids, metadatas, strict=False)
        }

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        result = self.collection.query(
            query_embeddings=[list(embedding)],  # type: ignore[arg-type]
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [
            VectorMatch(
                id=str(match_id),
                text=str(text or ""),
                metadata=dict(meta or {}),
                distance=float(distance),
            )
            for match_id, text, meta, distance in zip(
                ids, documents, metadatas, distances, strict=False
            )
        ]

    def count(self) -> int:
        return int(self.collection.count())

    def health(self) -> dict[str, Any]:
        return {
            "backend": "chromadb",
            "collection": self._collection_name,
            "persist_dir": str(self._persist_dir),
            "space": DISTANCE_SPACE,
            "count": self.count(),
        }

    # -- maintenance -------------------------------------------------------

    def delete_document(self, document_id: str, document_version: str | None = None) -> None:
        """Remove every chunk of a document (optionally of one version only).

        Needed for corpus updates and for the Phase 7 invalidation rules: when
        a document is withdrawn, its chunks must leave the index, not merely
        stop being cited.
        """
        where: dict[str, Any] = {"document_id": document_id}
        if document_version is not None:
            where = {"$and": [{"document_id": document_id}, {"document_version": document_version}]}
        self.collection.delete(where=where)

    def reset(self) -> None:
        """Drop the whole collection. Only used by explicit full rebuilds."""
        import chromadb

        if self._client is None:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        # The collection may simply not exist yet; dropping is best-effort.
        with suppress(Exception):
            self._client.delete_collection(self._collection_name)
        self._collection = None
