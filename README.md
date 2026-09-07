<div align="center">

---

## Why this exists

Most RAG demos stop at `documents → embeddings → vector search → LLM`. For an
*enterprise* assistant that path is both insufficient and unsafe: it misses exact
identifiers, has no access control, trusts client-supplied identity, forces
structured lookups through fuzzy similarity search, and happily fabricates
citations — all with no way to prove quality.

SecureCorp AI answers a harder question:

> **How do you build a RAG system an enterprise could actually trust — one that
> retrieves the right evidence, enforces who is allowed to see it, never
> fabricates a citation, and can prove its own quality with reproducible metrics?**

The secure request pipeline:

```
authentication → authorization → scope-aware cache → query routing
  → hybrid search (BM25 + dense) or authorized template-SQL
  → RRF → cross-encoder rerank → evidence validation
  → LLM generation → citation validation → response → cache
```

Authorization runs **before** retrieval — unauthorized content is never a
candidate, not retrieved-then-filtered. The LLM never decides authorization and
may cite only evidence IDs the application supplied.

---

## Measured results

All figures are real output from the offline harness, **authorization enforced**
(the production path), with RRF `k=10` and the identifier-aware reranker bypass
live. The eval assigns each query an identity actually authorized for its
expected documents, so the score measures *retrieval*, not the test user's
clearance — while `is_authorized` still runs on every retrieved chunk.

### Retrieval ablation — 80-query dev set

| Strategy               | Recall@5         | Hit@1  | MRR@10 | nDCG@10 |
| ---------------------- | ---------------- | ------ | ------ | ------- |
| Dense-only             | 85.00%           | 51.25% | 0.663  | 0.953   |
| BM25-only              | 92.50%           | 60.00% | 0.736  | 1.068   |
| **Hybrid (RRF)** | **95.00%** | 56.25% | 0.723  | 1.073   |
| Hybrid + Rerank        | 88.75%           | 56.25% | 0.707  | 0.929   |

Against a **measured achievable ceiling of 96.25%** (3 of 80 rows cite documents
no single-department identity can fully see), Hybrid-RRF at 95.00% is essentially
at the ceiling.

### Retrieval ablation — 64-item answerable holdout *(final reporting split)*

| Strategy               | Recall@5         | Hit@1  | MRR@10 | nDCG@10 |
| ---------------------- | ---------------- | ------ | ------ | ------- |
| Dense-only             | 84.38%           | 39.06% | 0.595  | 1.031   |
| BM25-only              | 85.94%           | 59.38% | 0.726  | 1.209   |
| **Hybrid (RRF)** | **90.62%** | 46.88% | 0.664  | 1.188   |
| Hybrid + Rerank        | 87.50%           | 53.12% | 0.672  | 0.991   |

### Generation, citations & security

| Metric                                 | Result                          |
| -------------------------------------- | ------------------------------- |
| Abstention on unanswerable questions   | **16 / 16 = 100%**        |
| Refusal of prompt-injection attempts   | **6 / 6 = 100%**          |
| Citation validity / invalid-ID rate    | **100% / 0%**             |
| Citation coverage                      | **95.7%**                 |
| Unauthorized chunks reaching the LLM   | **0** (enforced + tested) |
| Cross-tenant / role / dept cache reuse | **0** (scope-hashed keys) |

> **Integrity rule (enforced in code):** every number here comes from an actual
> harness run — no invented benchmarks. The landing page even has a unit test
> that fails if an unmeasured metric is smuggled into the UI.

---

## At a glance

|                         |                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **Corpus**        | 276 documents (from 260 Markdown files) · 455 chunks · 125,813 body tokens (exact, MiniLM tokenizer) |
| **Vector store**  | ChromaDB · 455 vectors · 384-dim · cosine (Chroma Cloud in deploy, behind an adapter)               |
| **Sparse**        | BM25Okapi · k1=1.5 · b=0.75                                                                          |
| **Fusion**        | Reciprocal Rank Fusion on unique`chunk_id` · k=10                                                   |
| **Reranker**      | cross-encoder/ms-marco-MiniLM-L6-v2 (bypassed for exact-ID queries)                                    |
| **Embeddings**    | sentence-transformers/all-MiniLM-L6-v2                                                                 |
| **Golden set**    | 343 dev · 71 holdout · 9 categories · never tuned on holdout                                        |
| **Quality gates** | `ruff` ✅ · `ruff format` ✅ · `mypy` ✅ · full test suite green                              |

---

## What makes it different

1. **Security-first RAG** — authorization *before* retrieval, with a hard,
   testable zero-leakage invariant. Most RAG demos have no access control at all.
2. **Genuinely hybrid** — BM25 + dense + RRF + cross-encoder, with a diagnostic
   that *proves* why (40/40 vs 4/40 on exact identifiers) and reaches 95% Recall@5.
3. **Right tool for the data** — structured questions route to safe template SQL,
   not forced through embeddings.
4. **Anti-hallucination by construction** — server-side citation validation and
   principled abstention (100% correct decline on unanswerable & injection cases).
5. **Evaluation-driven & honest** — reproducible metrics on a held-out set, an
   explicit rule against inventing numbers, and eval methodology that measures
   retrieval rather than the test user's clearance.
6. **Production-shaped** — streaming SSE API, scope-aware caching, config-driven,
   containerized, split-domain cloud deployment.

---

## Architecture

```text
                              USER
                                │
                                ▼
                       Authentication (JWT)
                                │
                                ▼
        Authorization Context (roles · dept · tenant · scope)
                                │
                                ▼
             Scope-aware cache  (L1 exact → L2 semantic)
                                │ (miss)
                                ▼
                        Query Classification
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                   ▼
       DOCUMENT_RAG       STRUCTURED_SQL          REFUSE
      (BM25 + dense,     (PostgreSQL, authz     (safe refusal)
       RRF, reranker)     template query)
             └──────────┬───────┘
                        ▼
        Reciprocal Rank Fusion (by unique chunk_id) → rerank → Top-K
                        ▼
              Evidence validation → LLM generation
                        ▼
            Citation validation (unknown IDs rejected)
                        ▼
              Secure response → cached with scope hash
```

**Invariants that are never broken:** RRF fuses on `chunk_id` (not
`document_id`); authorization precedes evidence; cached answers never cross
authorization scopes; every citation resolves to a real indexed chunk or record;
RAGAS/eval is offline only, never on the request path.

---

## Core capabilities

1. **Heterogeneous ingestion** — document-type-aware hierarchical chunking
   (source-specific atoms + shared token-budget packing) over policies, KB
   articles, emails, meetings, Slack threads, Jira issues, GitHub items.
2. **Hybrid retrieval** — BM25 sparse + dense vector, fused via RRF on
   `chunk_id`; dense over-fetches and is authorized by an `is_authorized`
   post-filter (not a lossy pre-filter).
3. **Cross-encoder reranking** — bounded candidate set; **bypassed for
   exact-identifier queries** where it otherwise demotes the right chunk.
4. **RBAC + ABAC** — roles (`employee|manager|hr|finance|it|admin`) plus
   attributes (`tenant_id`, `department`, `owner_user_id`); no superuser bypass.
5. **Scope-aware cache** — L1 exact + L2 semantic, keys hashed on auth scope so
   reuse can never cross a role/department/tenant boundary.
6. **Structured SQL path** — PostgreSQL via `psycopg[binary]`, template-based
   queries (no free-form text-to-SQL).
7. **Citation-validated generation** — every emitted citation validated
   server-side against real evidence; unknown IDs rejected; principled abstention.
8. **Offline evaluation** — deterministic retrieval metrics + RAGAS + citation /
   security / cache experiments, reproducible and never tuned on holdout.

---

## Getting started

```bash
# 1. Install (uv manages the venv + lockfile)
uv sync --extra api --extra retrieval

# 2. Build the corpus + indexes (writes data/processed and data/chroma_db)
uv run python scripts/build_registry.py
uv run python scripts/build_chunks.py
uv run python scripts/build_index.py

# 3. Quality gates
uv run ruff check .
uv run ruff format --check .
uv run mypy src
HYBRIDRAG_CHROMA_CLOUD=false uv run pytest

# 4. Run the backend (FastAPI + streaming SSE)
uv run uvicorn hybridrag.api.app:app --reload      # :8000

# 5. Run the frontend
cd web && npm install && npm run dev                # :3000
```

Copy `.env.example` → `.env` and fill in provider keys. All model names and
retrieval parameters are configurable via `HYBRIDRAG_*` env vars (see
`src/hybridrag/config.py`).

### Reproduce the evaluation

```bash
# 4-arm retrieval ablation (per-arm + per-category, JSON + CSV)
HYBRIDRAG_CHROMA_CLOUD=false uv run python scripts/run_ablation.py \
    --queries data/golden/answerable_holdout.jsonl \
    --report-json evaluation/reports/holdout.json

# validate the golden set schema / splits
uv run python scripts/audit_golden.py
```

---

## Repository structure

```
securecorp-ai-hybridrag/
├── CLAUDE.md  AGENTS.md  README.md  LICENSE
├── pyproject.toml  uv.lock  .env.example
├── Dockerfile  railway.toml            backend deploy (Railway)
│
├── docs/PROJECT_DOCUMENTATION.md        presentation brief + measured results
│
├── data/
│   ├── raw/                             276 documents in 260 Markdown files
│   ├── processed/{registry,chunks}.jsonl
│   ├── golden/{development,holdout}.jsonl   343 dev · 71 holdout
│   └── chroma_db/                       dense index (gitignored)
│
├── scripts/
│   ├── build_{registry,chunks,index}.py     corpus → chunks → ChromaDB
│   ├── audit_golden.py                       golden-set schema validator
│   ├── author_golden_expansion.py            grounded golden-query authoring
│   ├── run_ablation.py                       4-arm × per-category metrics
│   ├── seed_db.py                            PostgreSQL synthetic seeding
│   └── probe_*.py / run_ragas_*.py           reproducible eval probes
│
├── src/hybridrag/
│   ├── config.py                        Settings (env prefix HYBRIDRAG_)
│   ├── domain/models.py                 Document, Chunk, RankedChunk, enums
│   ├── ingestion/                       frontmatter, loaders, chunking, tokenization
│   ├── indexing/                        embeddings, chroma_store, bm25_store, pipeline
│   ├── retrieval/                       fusion, reranker, hybrid
│   ├── generation/                      provider, formatter, generator, abstention
│   ├── authorization/                   models, engine
│   ├── routing/  structured/  caching/  router · template-SQL · redis cache
│   ├── evaluation/                      retrieval_eval, citation/ragas/cache metrics
│   ├── assistant.py                     end-to-end orchestration
│   └── api/                             FastAPI routes + schemas (SSE chat, auth, analytics)
│
├── web/                                 Next.js 15 app (chat, dashboard, landing)
└── tests/                               unit · integration · evaluation · api · security
```

---

## Deployment

**Topology:** Next.js frontend on **Vercel**, FastAPI backend on **Railway**,
with Railway **managed Postgres + Redis** and **Chroma Cloud** for the dense
index. The backend builds from the root `Dockerfile` (see `railway.toml`).

### Railway — backend + data services

Add **Postgres** and **Redis** plugins, add the repo as a service (auto-detects
the `Dockerfile`), then set service variables:

```bash
# Data services (the app also reads Railway's native DATABASE_URL / REDIS_URL)
HYBRIDRAG_DATABASE_URL=${{Postgres.DATABASE_URL}}
HYBRIDRAG_REDIS_URL=${{Redis.REDIS_URL}}

# Secrets / providers
HYBRIDRAG_JWT_SECRET=<a long random secret>
HYBRIDRAG_GROQ_API_KEY=<groq key>
HYBRIDRAG_LLM_MODEL=openai/gpt-oss-120b        # any model your key can access

# Chroma Cloud (dense index)
HYBRIDRAG_CHROMA_CLOUD=true
HYBRIDRAG_CHROMA_API_KEY=<key>
HYBRIDRAG_CHROMA_TENANT=<tenant-uuid>
HYBRIDRAG_CHROMA_DATABASE=securecorp
HYBRIDRAG_CHROMA_SERVER_URL=api.trychroma.com

# Split-domain auth cookie (frontend and API on different origins)
HYBRIDRAG_CORS_ORIGINS=["https://<your-app>.vercel.app"]
HYBRIDRAG_AUTH_COOKIE_DOMAIN=
HYBRIDRAG_AUTH_COOKIE_SAMESITE=none
HYBRIDRAG_AUTH_COOKIE_SECURE=true
```

> The `preDeployCommand` (`python scripts/seed_db.py`) creates the schema and
> seeds synthetic records on each deploy — idempotent (`IF NOT EXISTS` +
> `ON CONFLICT DO NOTHING`). If Postgres isn't wired yet it logs a warning and
> **skips** (exit 0), so the deploy still succeeds in document-RAG-only mode.

### Vercel — frontend

Import the repo, set the project **root directory** to `web/`, and set:

```bash
NEXT_PUBLIC_API_BASE=https://<your-backend>.up.railway.app
```

> `NEXT_PUBLIC_*` is inlined at **build time**, so a change requires a redeploy.

### Verify

```bash
curl https://<your-backend>.up.railway.app/api/health
# {"status":"ok","retriever_wired":true,"redis_ok":true,"database_ok":true}
```

Open the Vercel URL, sign in as a demo user, and run a query — the cross-site
session cookie is sent because the API sets `SameSite=None; Secure`.

---

## Scenario (synthetic)

Everything is **fictional and synthetic** — no real private data is ever used.
The company is **NexaCore Solutions Pvt. Ltd.** (~250 employees; software
consulting, cloud & managed IT), with departments HR, Engineering, Finance,
Operations, Sales, IT & Security, and Admin, and document classifications
`public`, `department_internal`, `restricted`, `confidential`.

---

## License

MIT — see [LICENSE](LICENSE).

<div align="center">
<sub>SecureCorp AI — an enterprise GenAI / RAG project. Every metric is measured, not invented.</sub>
</div>
