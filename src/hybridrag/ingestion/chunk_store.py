"""Chunk corpus: build chunks for every registry document and persist them.

``data/processed/chunks.jsonl`` is the single normalized artifact that BOTH
the BM25 index and the ChromaDB dense index consume, which is what makes RRF
fusion over ``chunk_id`` well-defined (CLAUDE.md §7).

Raw documents remain the source of truth: bodies are re-read from
``source_uri`` rather than copied into the registry.
"""

import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from hybridrag.domain import Chunk
from hybridrag.ingestion.chunking import chunk_document
from hybridrag.ingestion.registry import DocumentRegistry


def build_chunks(
    registry: DocumentRegistry,
    *,
    target_tokens: int,
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int = 0,
) -> list[Chunk]:
    """Chunk every document in the registry, in deterministic document order."""
    chunks: list[Chunk] = []
    for item in sorted(registry.documents, key=lambda x: x.document.document_id):
        chunks.extend(
            chunk_document(
                item.document,
                item.body,
                target_tokens=target_tokens,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                min_tokens=min_tokens,
            )
        )
    return chunks


def save_chunks(chunks: list[Chunk], processed_dir: Path) -> Path:
    """Write ``chunks.jsonl`` (one Chunk per line, deterministic order)."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    path = processed_dir / "chunks.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(json.dumps(chunk.model_dump(mode="json"), sort_keys=True) + "\n")
    return path


def load_chunks(path: Path) -> Iterator[Chunk]:
    """Stream Chunks back from a saved ``chunks.jsonl``."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield Chunk.model_validate(json.loads(line))


def chunk_stats(chunks: list[Chunk]) -> dict[str, object]:
    """Summary statistics for reporting and regression tests."""
    if not chunks:
        return {"chunks": 0}
    tokens = sorted(c.token_count for c in chunks)
    per_source = Counter(c.source_type.value for c in chunks)
    return {
        "chunks": len(chunks),
        "documents": len({c.document_id for c in chunks}),
        "tokens_total": sum(tokens),
        "tokens_min": tokens[0],
        "tokens_median": tokens[len(tokens) // 2],
        "tokens_max": tokens[-1],
        "tokens_mean": round(sum(tokens) / len(tokens), 1),
        "per_source_type": dict(sorted(per_source.items())),
    }
