"""Build the chunk corpus from data/raw/ and report the result.

Usage:  uv run python scripts/build_chunks.py

Rebuilds the document registry, applies document-type-aware chunking, writes
data/processed/chunks.jsonl, and prints size statistics so the chunking
configuration can be inspected before indexing begins.
"""

from collections import Counter

from hybridrag.config import get_settings
from hybridrag.ingestion import DocumentRegistry, build_chunks, chunk_stats, save_chunks


def main() -> None:
    settings = get_settings()
    registry = DocumentRegistry.build(settings.raw_dir)
    chunks = build_chunks(
        registry,
        target_tokens=settings.chunk_target_tokens,
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
        min_tokens=settings.chunk_min_tokens,
    )
    path = save_chunks(chunks, settings.processed_dir)
    stats = chunk_stats(chunks)

    print(f"Documents: {stats['documents']}    Chunks: {stats['chunks']}")
    print(
        f"\nTokens per chunk — min {stats['tokens_min']}, median {stats['tokens_median']}, "
        f"mean {stats['tokens_mean']}, max {stats['tokens_max']}"
    )
    print(f"Total tokens: {stats['tokens_total']:,}")

    print("\nChunks per source type:")
    per_source = stats["per_source_type"]
    assert isinstance(per_source, dict)
    for source, count in per_source.items():
        print(f"  {source:<15} {count}")

    print("\nChunks per document (top 10):")
    counts = Counter(c.document_id for c in chunks)
    for doc_id, count in counts.most_common(10):
        print(f"  {doc_id:<20} {count}")

    singletons = sum(1 for count in counts.values() if count == 1)
    print(f"\nSingle-chunk documents: {singletons}")

    config = (
        f"target={settings.chunk_target_tokens} max={settings.chunk_max_tokens} "
        f"overlap={settings.chunk_overlap_tokens} min={settings.chunk_min_tokens}"
    )
    print(f"\nChunking config: {config}")
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
