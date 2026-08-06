"""Ingestion layer: raw corpus files → normalized Documents + JSONL registry."""

from hybridrag.ingestion.frontmatter import parse_frontmatter, split_slack_threads
from hybridrag.ingestion.loaders import LoadedDocument, load_file, load_generic, load_slack
from hybridrag.ingestion.registry import SOURCE_DIRS, DocumentRegistry, ValidationIssue

__all__ = [
    "SOURCE_DIRS",
    "DocumentRegistry",
    "LoadedDocument",
    "ValidationIssue",
    "load_file",
    "load_generic",
    "load_slack",
    "parse_frontmatter",
    "split_slack_threads",
]
