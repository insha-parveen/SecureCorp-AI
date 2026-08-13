"""FastAPI app factory for the SecureCorp AI HybridRAG Phase 9 MVP.

Lifespan wiring (per the plan):
  * Construct the singleton ``SecureCorpAssistant`` (cache, router, generator).
  * Construct the singleton ``HybridRetriever`` from BM25 + Chroma + reranker.
  * Wire them together via ``assistant.set_retriever(...)``.

If the retrieval stack cannot be imported (e.g., the ``retrieval`` extra
is not installed or the index is missing), the app still starts — but
the chat route returns an explanatory error. This keeps the
``/api/auth/*`` surface working for the login flow in degraded setups.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hybridrag.api.dependencies import AppState
from hybridrag.api.routes_analytics import router as analytics_router
from hybridrag.api.routes_auth import router as auth_router
from hybridrag.api.routes_chat import router as chat_router
from hybridrag.assistant import SecureCorpAssistant
from hybridrag.config import Settings, get_settings

logger = logging.getLogger(__name__)


DEFAULT_JWT_SECRET = "dev-only-insecure-jwt-secret-change-me"


def _wire_retriever(assistant: SecureCorpAssistant, settings: Settings) -> object | None:
    """Construct and attach a ``HybridRetriever`` if all extras are available.

    Returns the retriever on success, ``None`` on any failure (logged).
    """
    try:
        from hybridrag.indexing import (
            BM25Index,
            ChromaVectorStore,
            get_embedding_provider,
        )
        from hybridrag.retrieval.hybrid import HybridRetriever
        from hybridrag.retrieval.reranker import CrossEncoderReranker
    except Exception as exc:  # noqa: BLE001
        logger.warning("Retrieval stack not importable: %s", exc)
        return None

    try:
        embeddings = get_embedding_provider(settings)
        # Warm the embedding model + reranker so the first request is fast.
        embeddings.embed_query("warmup")
        bm25 = BM25Index.from_chunk_file(settings.processed_dir / "chunks.jsonl", settings=settings)
        store = ChromaVectorStore.from_settings(settings)
        reranker = CrossEncoderReranker.from_settings(settings)
        reranker.rerank("warmup", [])
        retriever = HybridRetriever(bm25, store, embeddings, reranker, settings=settings)
        assistant.set_retriever(retriever)
        return retriever
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not initialize retrieval stack: %s", exc)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize singletons on startup, log teardown on shutdown."""
    settings = get_settings()
    if settings.jwt_secret == DEFAULT_JWT_SECRET:
        logger.warning(
            "HYBRIDRAG_JWT_SECRET is the development default. "
            "Set a real secret via env in any deployed environment."
        )

    assistant = SecureCorpAssistant(settings=settings)
    state = AppState()
    state.settings = settings
    state.assistant = assistant

    # Ensure the structured-data schema exists (idempotent CREATE TABLE IF NOT
    # EXISTS, including the query_logs analytics table). Wrapped so the app
    # still boots when Postgres is unreachable — the structured/analytics
    # routes degrade gracefully in that case.
    from contextlib import suppress

    with suppress(Exception):
        assistant._db.initialize_schema()

    retriever = _wire_retriever(assistant, settings)
    state.retriever = retriever
    if retriever is not None:
        logger.info("HybridRetriever wired at startup.")
    else:
        logger.warning("HybridRetriever not wired. /api/chat will return a typed error.")

    app.state.settings = settings
    app.state.assistant = assistant
    app.state.retriever = retriever

    try:
        yield
    finally:
        # Close the database connection pool on shutdown.
        from contextlib import suppress

        with suppress(Exception):
            assistant._db.close()
        logger.info("Shutting down SecureCorp AI API.")


def create_app() -> FastAPI:
    """Build the FastAPI app with all routes + CORS for the local web/ dev server."""
    settings = get_settings()
    app = FastAPI(
        title="SecureCorp AI",
        version="0.1.0",
        description="Phase 9 MVP: streaming chat over the NexaCore HybridRAG pipeline.",
        lifespan=lifespan,
    )

    # CORS for the local Next.js dev server (localhost:3000 by default).
    # In production the Next.js app and FastAPI would share an origin or the
    # proxy would set CORS — this is the dev convenience.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(analytics_router)

    @app.get("/api/health")
    def get_health() -> dict[str, object]:
        """Liveness probe. Returns whether the retriever is wired and
        whether Redis and Postgres are reachable."""
        retriever = getattr(app.state, "retriever", None)
        assistant: SecureCorpAssistant | None = getattr(app.state, "assistant", None)

        # Check Redis connectivity via the cache's ping method.
        redis_ok = False
        if assistant is not None:
            try:
                redis_ok = assistant._cache.ping()
            except Exception:  # noqa: BLE001
                redis_ok = False

        # Check Postgres connectivity via the database manager's ping.
        db_ok = False
        if assistant is not None:
            try:
                db_ok = assistant._db.ping()
            except Exception:  # noqa: BLE001
                db_ok = False

        return {
            "status": "ok",
            "retriever_wired": retriever is not None,
            "redis_ok": redis_ok,
            "database_ok": db_ok,
        }

    return app


# Module-level instance for ``uvicorn hybridrag.api.app:app``.
app = create_app()
