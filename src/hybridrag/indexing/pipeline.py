"""The dense indexing pipeline: chunks.jsonl -> embeddings -> vector store.

This is the orchestration layer. It knows about chunks, an
:class:`~hybridrag.indexing.embeddings.EmbeddingProvider`, and a
:class:`~hybridrag.indexing.vector_store.VectorStore` — but nothing about
sentence-transformers or Chroma specifically, so it is fully unit-testable
against fakes and stays valid when either backend is replaced.

Incremental indexing
--------------------
Re-embedding an unchanged corpus is pure waste, so the pipeline diffs the
desired state against the stored state before doing any work:

* **skip**   — the stored fingerprint (``content_hash`` + embedding model)
  matches, so the vector is still valid;
* **upsert** — the chunk is new, its text changed, or the embedding model
  changed (identical text under a different model is a different vector space,
  and mixing spaces in one collection silently ruins retrieval);
* **delete** — the record is in the index but no longer in the corpus. Pruning
  is on by default: a stale chunk that survives in the index is retrievable
  evidence for a document that no longer says it, which is a correctness and,
  once withdrawn documents matter, a security problem.

``content_hash`` is what makes this safe: it is derived from the chunk text, so
any edit upstream changes it, and chunking is deterministic, so an unchanged
document produces byte-identical chunks and no churn.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from hybridrag.config import Settings, get_settings
from hybridrag.domain import Chunk
from hybridrag.indexing.chunk_metadata import encode_chunk, index_fingerprint, stored_fingerprint
from hybridrag.indexing.embeddings import EmbeddingProvider, get_embedding_provider
from hybridrag.indexing.vector_store import VectorRecord, VectorStore
from hybridrag.ingestion.chunk_store import load_chunks


@dataclass(frozen=True)
class IndexReport:
    """Outcome of one indexing run — printed by the CLI, asserted by tests."""

    total_chunks: int
    embedded: int
    skipped: int
    deleted: int
    embedding_model: str
    corpus_version: str
    collection_count: int

    @property
    def up_to_date(self) -> bool:
        """True when the run had nothing to do (the idempotency check)."""
        return self.embedded == 0 and self.deleted == 0


def _plan(
    chunks: Sequence[Chunk],
    stored: dict[str, dict[str, object]],
    embedding_model: str,
    *,
    prune: bool,
    force: bool,
) -> tuple[list[Chunk], list[str]]:
    """Split the corpus into "must (re)embed" and "must delete" sets."""
    to_embed: list[Chunk] = []
    for chunk in chunks:
        record = stored.get(chunk.chunk_id)
        fresh = record is not None and stored_fingerprint(record) == index_fingerprint(
            chunk, embedding_model=embedding_model
        )
        if force or not fresh:
            to_embed.append(chunk)

    if not prune:
        return to_embed, []
    current = {chunk.chunk_id for chunk in chunks}
    return to_embed, sorted(stored.keys() - current)


def _batched(items: Sequence[Chunk], size: int) -> Iterable[Sequence[Chunk]]:
    for start in range(0, len(items), max(size, 1)):
        yield items[start : start + max(size, 1)]


def index_chunks(
    chunks: Sequence[Chunk],
    *,
    store: VectorStore,
    provider: EmbeddingProvider,
    corpus_version: str,
    batch_size: int = 32,
    prune: bool = True,
    force: bool = False,
    progress: bool = False,
) -> IndexReport:
    """Bring the vector store in sync with ``chunks``.

    Embedding and upserting happen batch by batch rather than corpus-wide, so
    an interrupted run leaves a partially-updated index rather than losing all
    its work — and peak memory stays bounded by ``batch_size``.
    """
    stored = store.get_metadata()
    to_embed, to_delete = _plan(chunks, stored, provider.model_name, prune=prune, force=force)

    for batch in _batched(to_embed, batch_size):
        vectors = provider.embed_documents([chunk.text for chunk in batch])
        store.upsert(
            [
                VectorRecord(
                    id=chunk.chunk_id,
                    text=chunk.text,
                    metadata=encode_chunk(
                        chunk,
                        embedding_model=provider.model_name,
                        corpus_version=corpus_version,
                    ),
                    embedding=vector,
                )
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
        )
        if progress:  # pragma: no cover - CLI ergonomics only
            print(f"  embedded {len(batch)} chunks")

    if to_delete:
        store.delete(to_delete)

    return IndexReport(
        total_chunks=len(chunks),
        embedded=len(to_embed),
        skipped=len(chunks) - len(to_embed),
        deleted=len(to_delete),
        embedding_model=provider.model_name,
        corpus_version=corpus_version,
        collection_count=store.count(),
    )


def index_chunk_file(
    path: Path | None = None,
    *,
    settings: Settings | None = None,
    store: VectorStore | None = None,
    provider: EmbeddingProvider | None = None,
    prune: bool = True,
    force: bool = False,
    progress: bool = False,
) -> IndexReport:
    """Index ``data/processed/chunks.jsonl`` using configured components.

    The convenience entry point for the CLI. Every dependency is injectable so
    tests never touch the real model or the real Chroma directory.
    """
    from hybridrag.indexing.chroma_store import ChromaVectorStore

    cfg = settings or get_settings()
    chunk_path = path or cfg.processed_dir / "chunks.jsonl"
    if not chunk_path.exists():
        raise FileNotFoundError(
            f"{chunk_path} not found — run `uv run python scripts/build_chunks.py` first."
        )
    return index_chunks(
        list(load_chunks(chunk_path)),
        store=store or ChromaVectorStore.from_settings(cfg),
        provider=provider or get_embedding_provider(cfg),
        corpus_version=cfg.corpus_version,
        batch_size=cfg.embedding_batch_size,
        prune=prune,
        force=force,
        progress=progress,
    )
