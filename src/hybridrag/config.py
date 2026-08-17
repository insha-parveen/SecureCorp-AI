"""Application configuration.

All model names, retrieval parameters, and paths are configurable via
environment variables (prefix ``HYBRIDRAG_``) or a ``.env`` file, per the
architecture rule that nothing retrieval-related is hardcoded.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
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
    # Railway's managed Postgres exposes the native ``DATABASE_URL``; we also
    # accept our own ``HYBRIDRAG_DATABASE_URL``. AliasChoices is tried
    # left-to-right, so the prefixed name wins when both are set (lets you
    # override a platform-injected URL). When neither is set this falls back to
    # the local-dev default below. NOTE: giving a field a validation_alias
    # opts it out of env_prefix, which is exactly why the prefixed name must be
    # listed explicitly here.
    database_url: str = Field(
        default="postgresql://nexacore_admin:nexacore_password@localhost:5432/nexacore_db",
        validation_alias=AliasChoices("HYBRIDRAG_DATABASE_URL", "DATABASE_URL"),
    )

    # --- Cache (Redis) ---
    # Same aliasing as database_url: accept Railway's native ``REDIS_URL`` as
    # well as ``HYBRIDRAG_REDIS_URL`` (prefixed wins when both are set).
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("HYBRIDRAG_REDIS_URL", "REDIS_URL"),
    )
    cache_ttl: int = 3600  # 1 hour default
    semantic_cache_threshold: float = 0.95
    # Version stamps baked into every cache key. Bumping any of these
    # invalidates the affected cache cohort without a manual Redis flush.
    cache_prompt_version: str = "v1"
    # Whether the cache should be used at all. Set to false to bypass
    # Redis entirely (e.g., in tests or when Redis is unavailable).
    cache_enabled: bool = True
    # Max number of semantic-cache entries to scan per scope. Prevents
    # unbounded O(n) scans on active scopes.
    semantic_cache_max_scan: int = 500

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

    # --- Cloud ChromaDB (optional) ---
    chroma_cloud: bool = False
    chroma_api_key: str | None = None
    chroma_server_url: str | None = None
    chroma_tenant: str | None = None
    chroma_database: str = "securecorp"

    # --- BM25 / sparse index ---
    bm25_index_file: str = "bm25_index.json"
    bm25_remove_stopwords: bool = True
    bm25_expand_identifiers: bool = True
    bm25_top_n: int = 50
    # Okapi BM25 term-frequency saturation (k1) and length normalization (b).
    # Library defaults; re-tune against the golden set in Phase 8.
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    # Dense candidate pool. Larger than bm25_top_n because dense retrieval is
    # authorized by an is_authorized POST-filter (not a Chroma pre-filter, see
    # retrieval/hybrid.py): over-fetching gives that post-filter enough
    # candidates to keep after unauthorized ones are dropped. Measured on the
    # 80q set (auth-on): raising 50->150 with no pre-filter lifts Dense-Only
    # ~30%->76% and Hybrid-RRF ~64%->85%, for ~11ms extra.
    dense_top_n: int = 150
    # RRF k tuned on the dev/legacy golden sets (2026-08): the library-default
    # k=60 flattens the 1/(k+rank) weights so much that fusion scored BELOW
    # its own dense/BM25 inputs. k=10 restores fusion's top-rank advantage and
    # lets it beat both inputs (measured: Recall@5 80%->~90% on the 80q set).
    rrf_k: int = 10
    # Cross-encoder candidate window. 30 was strictly dominated by 15 on the
    # golden set: 15 gave HIGHER Recall@5 (90% vs 88.75%) at ~2.4x lower
    # latency, because reranking >15 candidates feeds the cross-encoder
    # distractors that push good docs out of the top-5.
    rerank_candidates: int = 15
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

    # --- API / auth (Phase 9 MVP) ---
    # Self-issued JWT secret. The default is for local dev only; set via env
    # in any deployed environment. Startup logs a warning if the default is
    # in use (api/app.py).
    jwt_secret: str = "dev-only-insecure-jwt-secret-change-me"
    jwt_ttl_seconds: int = 3600
    # Cookie name for the session JWT.
    auth_cookie_name: str = "sc_auth"
    # Cookie domain for the session JWT. "localhost" lets the browser attach
    # the cookie across localhost ports (dev :3000 ↔ :8000). Set to empty via
    # env (HYBRIDRAG_AUTH_COOKIE_DOMAIN=) to use the exact request host — e.g.
    # in tests or behind a single production proxy origin.
    auth_cookie_domain: str | None = "localhost"
    # SameSite policy for the session cookie. "lax" is correct for a
    # single-origin or shared-parent-domain deploy. For a SPLIT deploy where
    # the web app and API are on different domains (e.g. two *.up.railway.app
    # hosts), the browser only sends the cookie on the cross-site /api/chat
    # request when SameSite=None — and SameSite=None REQUIRES Secure=true
    # (HTTPS). Set HYBRIDRAG_AUTH_COOKIE_SAMESITE=none and
    # HYBRIDRAG_AUTH_COOKIE_SECURE=true in that case.
    auth_cookie_samesite: str = "lax"
    # Whether the session cookie carries the Secure flag (HTTPS-only). Off in
    # local dev (HTTP); MUST be true in any HTTPS deployment, and is mandatory
    # when auth_cookie_samesite="none".
    auth_cookie_secure: bool = False
    # CORS origins allowed for the API (dev default: localhost:3000).
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

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
        if self.chunk_min_tokens > self.chunk_max_tokens:
            raise ValueError(
                f"chunk_min_tokens ({self.chunk_min_tokens}) > "
                f"chunk_max_tokens ({self.chunk_max_tokens}); the heading-merge "
                "guard can never fire and small chunks will never coalesce."
            )
        if self.chunk_target_tokens < self.chunk_min_tokens:
            raise ValueError(
                f"chunk_target_tokens ({self.chunk_target_tokens}) < "
                f"chunk_min_tokens ({self.chunk_min_tokens}); pack() will never "
                "reach the merge threshold and chunks will undershoot forever."
            )
        return self

    @model_validator(mode="after")
    def _auth_cookie_flags_are_coherent(self) -> "Settings":
        """Reject cookie settings the browser would silently drop.

        ``SameSite`` must be one of the three legal values, and the spec makes
        ``SameSite=None`` conditional on ``Secure`` — a None-without-Secure
        cookie is rejected by every modern browser, which would look like a
        broken login rather than a config error. Fail loudly at startup.
        """
        normalized = self.auth_cookie_samesite.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError(
                f"auth_cookie_samesite ({self.auth_cookie_samesite!r}) must be "
                "one of 'lax', 'strict', or 'none'."
            )
        object.__setattr__(self, "auth_cookie_samesite", normalized)
        if normalized == "none" and not self.auth_cookie_secure:
            raise ValueError(
                "auth_cookie_samesite='none' requires auth_cookie_secure=true "
                "(browsers reject a cross-site cookie without the Secure flag). "
                "Set HYBRIDRAG_AUTH_COOKIE_SECURE=true for a split HTTPS deploy."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
