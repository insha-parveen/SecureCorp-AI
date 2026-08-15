# Backend Dockerfile for SecureCorp AI FastAPI service.
#
# Two-stage build: the builder resolves the locked dependency set into a
# virtualenv and pre-caches the embedding/reranker models; the runner is a
# slim image that carries only the venv, the source, the BM25 corpus, and
# the model cache. The dense index is served from Chroma Cloud, so no local
# vector store ships in the image.
FROM python:3.11-slim AS builder

WORKDIR /app

# uv resolves and installs from the committed uv.lock.
RUN pip install --no-cache-dir uv

# Dependency manifests first so the (slow) dependency layer is cached and
# only re-runs when the lockfile changes, not on every source edit.
COPY pyproject.toml uv.lock README.md ./

# Phase 1: install ONLY third-party dependencies. --no-install-project means
# the project's own package is skipped here (src/ isn't present yet), and
# --frozen makes uv honor uv.lock exactly and fail if it is stale.
RUN uv sync --extra api --extra retrieval --no-dev --frozen --no-install-project

# Source and the runtime data the app reads. .dockerignore keeps
# data/chroma_db (Chroma Cloud in deployment) and host caches out.
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Phase 2: now that src/ is present, install the project itself into the venv.
RUN uv sync --extra api --extra retrieval --no-dev --frozen

# Pre-download the sentence-transformers embedding + cross-encoder reranker
# into a baked HF cache so the first request doesn't pay the download cost
# (and risk the deploy health-check timeout). Best-effort: a transient
# network failure at build time must not fail the deploy — the app falls
# back to downloading at startup. Override the args to match config if you
# swap models. The two ENVs feed both this pre-cache and the runtime app.
ARG HYBRIDRAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ARG HYBRIDRAG_RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L6-v2
ENV HF_HOME=/app/hf-cache \
    HYBRIDRAG_EMBEDDING_MODEL=${HYBRIDRAG_EMBEDDING_MODEL} \
    HYBRIDRAG_RERANKER_MODEL=${HYBRIDRAG_RERANKER_MODEL}
RUN mkdir -p "$HF_HOME" && /app/.venv/bin/python -c "\
import os; \
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer(os.environ['HYBRIDRAG_EMBEDDING_MODEL']); \
CrossEncoder(os.environ['HYBRIDRAG_RERANKER_MODEL'])" \
    || echo "WARN: model pre-cache skipped; will download at first request"

# --- Production stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
# Read the models from the baked cache instead of hitting the network.
ENV HF_HOME=/app/hf-cache
# CPU-only box: never probe for CUDA (the CPU torch wheel wouldn't find it
# anyway, but this silences the probe and keeps startup deterministic).
ENV HYBRIDRAG_EMBEDDING_DEVICE=cpu

# Copy the resolved venv, source, runtime data, and model cache from builder.
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/data ./data
COPY --from=builder /app/hf-cache ./hf-cache

# Non-root runtime user.
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Railway injects $PORT and routes to it; fall back to 8000 for local runs.
# EXPOSE is documentation only; the CMD is what must honor $PORT.
EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime (exec form would pass the
# literal string). Railway sets PORT; docker-compose/local default to 8000.
CMD ["sh", "-c", "uvicorn hybridrag.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
