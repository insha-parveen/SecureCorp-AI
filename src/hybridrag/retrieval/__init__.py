"""Retrieval orchestration: RRF fusion, cross-encoder reranking, hybrid retriever.

Phase 3. The package exposes the RRF fusion and reranking primitives plus
``HybridRetriever``, which composes BM25 + dense retrieval → RRF → rerank.
"""

from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import (
    CrossEncoderReranker,
    Reranker,
    rerank_top,
)

__all__ = [
    "CrossEncoderReranker",
    "HybridRetriever",
    "Reranker",
    "rerank_top",
    "rrf_fuse",
]
