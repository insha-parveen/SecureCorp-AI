"""Build the document registry from data/raw/ and report the result.

Usage:  uv run python scripts/build_registry.py

Walks the raw corpus, normalizes every file into Documents, runs validation,
writes data/processed/registry.jsonl + registry_issues.jsonl, and prints a
summary so ingestion output can be inspected before chunking begins.
"""

from collections import Counter

from hybridrag.config import get_settings
from hybridrag.ingestion import DocumentRegistry


def main() -> None:
    settings = get_settings()
    registry = DocumentRegistry.build(settings.raw_dir)
    registry_path, issues_path = registry.save(settings.processed_dir)

    print(f"Documents ingested: {len(registry)}")
    print("\nPer source type:")
    for source, count in registry.stats().items():
        print(f"  {source:<15} {count}")

    total_words = sum(d.document.word_count for d in registry.documents)
    total_tokens = sum(d.document.estimated_tokens for d in registry.documents)
    print(f"\nTotal words: {total_words:,}   estimated tokens: {total_tokens:,}")

    severity_counts = Counter(issue.severity for issue in registry.issues)
    print(f"\nValidation issues: {dict(severity_counts) or 'none'}")
    for issue in registry.issues:
        print(f"  [{issue.severity}] {issue.document_id or issue.source_uri}: {issue.message}")

    print(f"\nSaved: {registry_path}")
    print(f"Saved: {issues_path}")


if __name__ == "__main__":
    main()
