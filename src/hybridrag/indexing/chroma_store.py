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
from typing import TYPE_CHECKING, Any, cast

from hybridrag.config import Settings, get_settings
from hybridrag.indexing.vector_store import VectorMatch, VectorRecord

if TYPE_CHECKING:  # pragma: no cover - typing only
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection
    from chromadb.api.types import Embeddings

#: Distance metric for the collection; see the module docstring.
DISTANCE_SPACE = "cosine"


class ChromaVectorStore:
    """Persistent, local-first Chroma collection behind the store interface."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
        *,
        chroma_cloud: bool = False,
        chroma_api_key: str | None = None,
        chroma_server_url: str | None = None,
        chroma_tenant: str | None = None,
        chroma_database: str | None = None,
    ) -> None:
        self._persist_dir = persist_dir
        # Resolve to a concrete collection name. Every real caller supplies one
        # (from_settings passes cfg.chroma_collection; direct constructions pass
        # a literal), but the optional param defaulted to None, which would make
        # get_or_create_collection(name=None) fail deep inside Chroma. Fall back
        # to the configured default so the attribute is a firm ``str`` invariant.
        self._collection_name: str = collection_name or get_settings().chroma_collection
        self._client: ClientAPI | None = None
        self._collection: Collection | None = None
        self._chroma_cloud = chroma_cloud
        self._chroma_api_key = chroma_api_key
        self._chroma_server_url = chroma_server_url
        self._chroma_tenant = chroma_tenant
        self._chroma_database = chroma_database

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "ChromaVectorStore":
        cfg = settings or get_settings()
        return cls(
            persist_dir=cfg.chroma_dir,
            collection_name=cfg.chroma_collection,
            chroma_cloud=cfg.chroma_cloud,
            chroma_api_key=cfg.chroma_api_key,
            chroma_server_url=cfg.chroma_server_url,
            chroma_tenant=cfg.chroma_tenant,
            chroma_database=cfg.chroma_database,
        )

    # -- lazy connection ---------------------------------------------------

    def _connect(self) -> "ClientAPI":
        """Create and return a Chroma client (cloud or local)."""
        import chromadb

        if self._chroma_cloud:
            # Chroma Cloud via the native CloudClient (chromadb >= 1.x).
            # Signature: CloudClient(tenant, database, api_key, *,
            #                       cloud_host='api.trychroma.com', cloud_port=443,
            #                       enable_ssl=True)
            return chromadb.CloudClient(
                tenant=self._chroma_tenant or "",
                database=self._chroma_database or "securecorp",
                api_key=self._chroma_api_key,
                cloud_host=self._chroma_server_url or "api.trychroma.com",
                cloud_port=443,
                enable_ssl=True,
            )
        else:
            # Local persistent mode requires a directory. In cloud mode this is
            # never reached; guard here so a misconfigured local store fails with
            # a clear message instead of an AttributeError on None.
            if self._persist_dir is None:
                raise ValueError(
                    "persist_dir is required for local ChromaDB (chroma_cloud=False). "
                    "Set HYBRIDRAG_CHROMA_DIR, or enable HYBRIDRAG_CHROMA_CLOUD."
                )
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(path=str(self._persist_dir))

    @property
    def collection(self) -> "Collection":
        """Open the persistent collection on first use.

        Lazy so that importing the indexing package — which the CLI and tests
        do — never creates ``data/chroma_db/`` as a side effect.
        """
        if self._collection is None:
            self._client = self._connect()
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
        # Chroma's ``Embeddings`` type is invariant over the vector element type;
        # our plain ``list[list[float]]`` satisfies the runtime contract but not
        # the invariant static type, so cast at this one SDK boundary.
        self.collection.upsert(
            ids=[r.id for r in records],
            documents=[r.text for r in records],
            metadatas=[r.metadata for r in records],
            embeddings=cast("Embeddings", [r.embedding for r in records]),
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
            query_embeddings=cast("Embeddings", [list(embedding)]),
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
        if self._client is None:
            self._client = self._connect()
        # The collection may simply not exist yet; dropping is best-effort.
        with suppress(Exception):
            self._client.delete_collection(self._collection_name)
        self._collection = None
