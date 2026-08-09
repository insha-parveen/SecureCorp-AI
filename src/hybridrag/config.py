"""Application configuration.

All model names, retrieval parameters, and paths are configurable via
environment variables (prefix ``HYBRIDRAG_``) or a ``.env`` file, per the
architecture rule that nothing retrieval-related is hardcoded.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the HybridRAG application."""

    model_config = SettingsConfigDict(
        env_prefix="HYBRIDRAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Paths ---
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    chroma_dir: Path = Path("data/chroma_db")

    # --- Models (baselines per CLAUDE.md; override via env) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    llm_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"
    groq_api_key: str | None = None
    openai_api_key: str | None = None

    # --- Database (PostgreSQL) ---
    # Railway provides this as DATABASE_URL. For local docker:
    # postgresql://nexacore_admin:nexacore_password@localhost:5432/nexacore_db
    database_url: str = "postgresql://nexacore_admin:nexacore_password@localhost:5432/nexacore_db"

    # --- Cache (Redis) ---
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600  # 1 hour default
    semantic_cache_threshold: float = 0.95

    # --- Embedding / dense index ---
    # Asymmetric models (e5, bge, ...) need different prefixes for passages and
    # queries. Empty for the MiniLM baseline; set via env when swapping models.
    embedding_document_prefix: str = ""
    embedding_query_prefix: str = ""
    embedding_batch_size: int = 32
    # Cosine is the metric the MiniLM baseline is trained for; normalizing at
    # encode time keeps cosine and inner product equivalent.
    embedding_normalize: bool = True
    # None -> let sentence-transformers pick (cuda when available, else cpu).
    embedding_device: str | None = None
    chroma_collection: str = "nexacore_chunks"

    # --- BM25 / sparse index ---
    bm25_index_file: str = "bm25_index.json"
    bm25_remove_stopwords: bool = True
    bm25_expand_identifiers: bool = True
    bm25_top_n: int = 50
    # Okapi BM25 term-frequency saturation (k1) and length normalization (b).
    # Library defaults; re-tune against the golden set in Phase 8.
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    dense_top_n: int = 50
    rrf_k: int = 60
    rerank_candidates: int = 30
    final_top_k: int = 5

    # Hard input limit of the embedding model, including the 2 special tokens
    # it adds. Anything longer is SILENTLY TRUNCATED at encode time, so this is
    # the ceiling every chunking parameter below must respect.
    embedding_max_tokens: int = 512

    # --- Chunking parameters ---
    # Measured with the embedding model's own tokenizer (not an estimate), and
    # bounded so that overlap + max_tokens stays under embedding_max_tokens.
    chunk_target_tokens: int = 440
    chunk_max_tokens: int = 440
    chunk_overlap_tokens: int = 60
    # Below this size a heading boundary does NOT end a chunk: consecutive
    # small sections merge instead, so heading-dense policies don't produce a
    # swarm of tiny chunks that wreck BM25 term statistics and embedding
    # quality alike. A real value to re-tune in the Phase 8 chunking sweep.
    chunk_min_tokens: int = 300

    # --- Corpus versioning (bump when raw corpus changes; used by cache keys) ---
    corpus_version: str = "2026-08-corpus-v2"

    @model_validator(mode="after")
    def _chunks_must_fit_the_embedding_model(self) -> "Settings":
        """Reject any configuration that would produce truncated chunks.

        A packed chunk can reach ``overlap + max`` tokens (carried overlap plus
        one full-size atom), and the model reserves 2 slots for special tokens.
        Truncation is silent, so this has to fail loudly at startup instead.
        """
        worst_case = self.chunk_overlap_tokens + self.chunk_max_tokens
        budget = self.embedding_max_tokens - 2
        if worst_case > budget:
            raise ValueError(
                f"chunk_overlap_tokens + chunk_max_tokens = {worst_case} exceeds the "
                f"{budget}-token budget of {self.embedding_model}; chunks would be "
                "silently truncated at encode time."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
