"""Build (or refresh) the dense ChromaDB index from data/processed/chunks.jsonl.

Usage:
    uv run python scripts/build_index.py            # incremental
    uv run python scripts/build_index.py --force    # re-embed everything
    uv run python scripts/build_index.py --no-prune # keep records missing from the corpus
    uv run python scripts/build_index.py --stats    # report only, index nothing

Incremental by default: chunks whose text and embedding model are unchanged are
skipped, so re-running after editing a handful of documents costs a handful of
embeddings, not 387.
"""

import argparse

from hybridrag.config import get_settings
from hybridrag.indexing import ChromaVectorStore, index_chunk_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-embed every chunk")
    parser.add_argument(
        "--no-prune",
        dest="prune",
        action="store_false",
        help="do not delete indexed records that are absent from chunks.jsonl",
    )
    parser.add_argument("--stats", action="store_true", help="print index health and exit")
    args = parser.parse_args()

    settings = get_settings()

    if args.stats:
        store = ChromaVectorStore.from_settings(settings)
        for key, value in store.health().items():
            print(f"{key:<14} {value}")
        return

    print(f"Embedding model: {settings.embedding_model}")
    print(f"Collection:      {settings.chroma_collection} ({settings.chroma_dir})")
    report = index_chunk_file(force=args.force, prune=args.prune, progress=True)

    print(
        f"\nChunks: {report.total_chunks}    embedded {report.embedded}    "
        f"skipped {report.skipped}    deleted {report.deleted}"
    )
    print(f"Collection size: {report.collection_count}")
    print(f"Corpus version:  {report.corpus_version}")
    if report.up_to_date:
        print("Index already up to date — nothing re-embedded.")


if __name__ == "__main__":
    main()
