# SecureCorp AI — HybridRAG + Reranking

A secure enterprise knowledge assistant over the synthetic NexaCore Solutions corpus.

**Retrieval architecture:** BM25 + dense (ChromaDB) hybrid search → Reciprocal Rank Fusion → cross-encoder reranking, with RBAC/ABAC authorization enforced before evidence reaches the LLM, authorization-aware caching, SQL routing for structured records, server-side citation validation, and offline evaluation (deterministic retrieval metrics + RAGAS).

## Status

Implementation in progress. Phase 1 (synthetic corpus + golden evaluation sets) is complete; core schemas and ingestion are being built.

for the full architecture specification and `docs/company_bible.md` for the canonical corpus reference.

## Development

```bash
uv sync                 # create/refresh environment
uv run pytest           # tests
uv run ruff check .     # lint
uv run mypy src         # types
```

No benchmark numbers are reported until produced by actual experiments.
