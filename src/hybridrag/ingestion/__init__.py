"""Ingestion layer: raw corpus files → normalized Documents → Chunks."""

from hybridrag.ingestion.chunk_store import (
    build_chunks,
    chunk_stats,
    load_chunks,
    save_chunks,
)
from hybridrag.ingestion.chunking import Atom, atomize, chunk_document, pack_atoms
from hybridrag.ingestion.frontmatter import parse_frontmatter, split_slack_threads
from hybridrag.ingestion.loaders import LoadedDocument, load_file, load_generic, load_slack
from hybridrag.ingestion.registry import SOURCE_DIRS, DocumentRegistry, ValidationIssue
from hybridrag.ingestion.structure import Section, parse_sections
from hybridrag.ingestion.tokenization import count_tokens, split_paragraphs, split_sentences

__all__ = [
    "SOURCE_DIRS",
    "Atom",
    "DocumentRegistry",
    "LoadedDocument",
    "Section",
    "ValidationIssue",
    "atomize",
    "build_chunks",
    "chunk_document",
    "chunk_stats",
    "count_tokens",
    "load_chunks",
    "load_file",
    "load_generic",
    "load_slack",
    "pack_atoms",
    "parse_frontmatter",
    "parse_sections",
    "save_chunks",
    "split_paragraphs",
    "split_sentences",
    "split_slack_threads",
]
