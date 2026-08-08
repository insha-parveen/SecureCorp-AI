"""Index construction: embeddings, the dense vector store, BM25, and the pipeline.

Public surface for the rest of the application. Callers should import from
``hybridrag.indexing`` rather than reaching into ``chroma_store`` or
``embeddings`` directly, so backend swaps stay contained to this package.
"""

from hybridrag.indexing.bm25_store import BM25Index, analyze
from hybridrag.indexing.chroma_store import ChromaVectorStore
from hybridrag.indexing.chunk_metadata import (
    decode_chunk,
    encode_chunk,
    index_fingerprint,
    stored_fingerprint,
)
from hybridrag.indexing.embeddings import (
    EmbeddingProvider,
    SentenceTransformerEmbeddings,
    get_embedding_provider,
)
from hybridrag.indexing.pipeline import IndexReport, index_chunk_file, index_chunks
from hybridrag.indexing.vector_store import VectorMatch, VectorRecord, VectorStore

__all__ = [
    "BM25Index",
    "ChromaVectorStore",
    "EmbeddingProvider",
    "IndexReport",
    "SentenceTransformerEmbeddings",
    "VectorMatch",
    "VectorRecord",
    "VectorStore",
    "analyze",
    "decode_chunk",
    "encode_chunk",
    "get_embedding_provider",
    "index_chunk_file",
    "index_chunks",
    "index_fingerprint",
    "stored_fingerprint",
]
