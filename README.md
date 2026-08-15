# SecureCorp AI

## HybridRAG + Reranking

**🔐 An enterprise knowledge assistant with authorization-aware retrieval, citation validation, and offline evaluation.**

<img src="images/logo.svg" alt="SecureCorp AI" width="110"/>

## 📊 At a Glance

| Metric                    | Value                                       |
| ------------------------- | ------------------------------------------- |
| **Documents**       | 275 (from 260 Markdown files)               |
| **Chunks**          | 450                                         |
| **Body Tokens**     | 124,472 (MiniLM tokenizer)                  |
| **Vector Store**    | ChromaDB • 450 vectors • 384 dims         |
| **Backend Tests**   | **211 passed**                        |
| **Quality Gates**   | ✅ ruff • ✅ mypy • ✅ format (348 files) |
| **Embedding Model** | sentence-transformers/all-MiniLM-L6-v2      |
| **Reranker**        | cross-encoder/ms-marco-MiniLM-L6-v2         |
| **BM25**            | k1=1.5, b=0.75 (library defaults)           |

---

## 🧪 Evaluation

The offline evaluation harness measures retrieval and generation quality. Metrics are computed over the golden dev/holdout sets — never tuned on holdout data.

### Retrieval Metrics (per strategy)

| Strategy                                | Recall@5  | Recall@10 | Hit@5     | MRR@10    | nDCG@10   |
| --------------------------------------- | --------- | --------- | --------- | --------- | --------- |
| **Dense-only**                    | measured* | measured* | measured* | measured* | measured* |
| **BM25-only**                     | measured* | measured* | measured* | measured* | measured* |
| **Hybrid (BM25+Dense RRF)**       | measured* | measured* | measured* | measured* | measured* |
| **Hybrid + Cross-Encoder Rerank** | measured* | measured* | measured* | measured* | measured* |

*Actual values computed by `uv run run_retrieval_eval.py` — see `evaluation/` for per-category breakdowns.

### Generation Metrics (RAGAS)

| Metric                      | Description                            |
| --------------------------- | -------------------------------------- |
| **Faithfulness**      | Answer supported by retrieved evidence |
| **Answer Relevancy**  | LLM answer addresses the query         |
| **Context Precision** | Retrieved chunks relevant to answers   |
| **Context Recall**    | Retrieved chunks cover answer scope    |

### Citation Metrics

| Metric                              | Value                                |
| ----------------------------------- | ------------------------------------ |
| **Citation Validity Rate**    | validated server-side                |
| **Unsupported Citation Rate** | rejected/invalid IDs removed         |
| **Citation Coverage**         | % of answers with ≥1 valid citation |

### Security Metrics

| Metric                                     | Invariant                     |
| ------------------------------------------ | ----------------------------- |
| **Unauthorized chunks reaching LLM** | **0** (enforced)        |
| **Cross-user cache leakage**         | blocked by scope-hashed keys  |
| **Cross-role cache leakage**         | blocked by RBAC in cache keys |

> **Never tune on the holdout set.** Development data (`development.jsonl`: 283 items) is separate from final reporting data (`holdout.jsonl`: 71 items).

---

## 🏗️ Architecture

```text
USER → AUTH → AUTHORIZATION → QUERY ROUTER
                                      │
         ┌────────────────────────┼───────────────────────┐
         ▼                        ▼                       ▼
   DOCUMENT RAG          STRUCTURED SQL          REFUSE
   (Hybrid: BM25+Dense,     (PostgreSQL, authz)    (safe refusal)
    RRF, Reranker)          (query results)           response
                                      │
                                      ▼
                           GENERATION (Groq LLM)
                                      │
                                      ▼
                       CITATION VALIDATION
                                      │
                                      ▼
                          FINAL RESPONSE
```

**Key invariants:** RRF on `chunk_id` not `document_id`; authorization before evidence; cache scope includes auth context; LLM never decides authorization.

---

## 🚀 Core Capabilities

1. **Heterogeneous ingestion** — Markdown-aware hierarchical chunking (atoms + packing)
2. **Hybrid retrieval** — BM25 sparse + dense vector → RRF fusion
3. **Cross-encoder reranking** — Bounded candidate set (top 20–50), ms-marco-MiniLM-L6-v2
4. **RBAC + ABAC** — Roles `employee|manager|hr|finance|it|admin` + attributes (`tenant_id`, `department`, `owner_user_id`)
5. **Secure cache** — L1 exact + L2 semantic, scope-hashed keys, RBAC-aware, TTL invalidation
6. **Structured SQL** — PostgreSQL via psycopg[binary], template-based query path (not free-form SQL)
7. **Citation-validated generation** — Server-side evidence validation; unknown citation IDs rejected
8. **Offline evaluation** — RAGAS + deterministic retrieval metrics + ablation studies
9. **Vector-store adapter** — Provider-agnostic (ChromaDB default, Pinecone migratable)
10. **Full CI readiness** — formatting/lint/typecheck/tests on every PR

---

## 📁 Repository Structure

```
securecorp-ai-hybridrag/
├── AGENTS.md  CLAUDE.md  README.md  LICENSE
├── pyproject.toml  uv.lock  .env.example  .gitignore
├── docs/company_bible.md
│
├── evaluation/
│   ├── golden_set/{qa_pairs,qa_pairs_hard}.json
│   ├── retrieval_eval/{retrieval_queries,expected_chunks}.json
│   └── security_eval/{rbac_queries,forbidden_queries}.json
│
├── data/
│   ├── raw/                           275 documents in 260 Markdown files
│   ├── processed/{registry,registry_issues,chunks}.jsonl
│   ├── golden/                        Phase 8 golden set (JSONL)
│   │   ├── development.jsonl          283 items, 9 categories
│   │   └── holdout.jsonl              71 items, 9 categories
│   ├── sweep/                         chunking-sweep artifacts
│   └── chroma_db/                     dense index (gitignored)
│
├── scripts/
│   ├── build_registry.py              raw corpus → registry.jsonl
│   ├── build_chunks.py                registry   → chunks.jsonl
│   ├── build_index.py                 chunks.jsonl → ChromaDB
│   ├── build_golden.py                Phase 8: bootstrap+hand-fill
│   ├── audit_golden.py                Phase 8: validate golden set schema
│   ├── seed_db.py                     PostgreSQL synthetic seeding
│   ├── run_retrieval_eval.py          overall 4-arm metrics
│   ├── run_ablation.py                Phase 8: 4-arm × per-category
│   ├── run_ragas.py                   Phase 8: RAGAS adapter
│   ├── run_chunking_sweep.py          Phase 8: 4-cell sweep
│   ├── run_cache_experiments.py       Phase 8: hit rate + isolation
│   └── run_phase8_eval.py             Phase 8: orchestrator + HTML report
│
├── src/hybridrag/
│   ├── config.py                      Settings (env prefix HYBRIDRAG_)
│   ├── domain/models.py               Document, Chunk, RankedChunk, enums
│   ├── ingestion/                     frontmatter, loaders, registry,
│   │                                  structure, tokenization, chunking
│   ├── indexing/                      embeddings, vector_store, chroma_store,
│   │                                  chunk_metadata, bm25_store, pipeline
│   ├── retrieval/                     fusion, reranker, hybrid
│   ├── generation/                    provider, formatter, generator
│   ├── authorization/                 models, engine
│   ├── routing/                       router
│   ├── structured/                    db, query_path
│   ├── caching/                       redis_cache, history
│   ├── evaluation/                    retrieval_eval, citation_metrics,
│   │                                  ragas_adapter, ragas_runner,
│   │                                  redis_cache_eval, html_report
│   ├── assistant.py                   end-to-end orchestration
│   └── api/                           FastAPI routes + schemas
│
└── tests/
    ├── unit/                          test_config, test_domain_models,
    │                                  test_frontmatter, test_loaders,
    │                                  test_registry, test_structure,
    │                                  test_chunking, test_indexing, test_bm25
    ├── integration/test_chroma_store.py   real Chroma, fake vectors
    ├── test_structured.py             test_cache.py  test_abstention.py
    ├── security/                      (stub)
    └── evaluation/                    test_retrieval_eval_metrics,
                                       test_citation_metrics,
                                       test_ragas_adapter,
                                       test_redis_cache_eval,
                                       test_html_report,
                                       test_phase8_smoke
```

---

## 🛠️ Development Workflow

```bash
# Install
uv sync

# Quality gates (all pass)
uv run pytest              # 211 passed, 1 skipped (PHASE8_RUN smoke)
uv run ruff check .        # clean
uv run ruff format --check .  # clean (348 files formatted)
uv run mypy src            # clean (44 source files, no issues)

# Run the backend
uv run uvicorn src.hybridrag.api.main:app --reload

# Run the frontend
cd web && npm install && npm run dev  # localhost:3000
```

---

## 🚀 Deployment

**Topology:** Next.js frontend on **Vercel**, FastAPI backend on **Railway**,
with Railway **managed Postgres + Redis** and **Chroma Cloud** for the dense
index. The backend builds from the root `Dockerfile` (see `railway.toml`); the
frontend builds from `web/Dockerfile` / Vercel's native Next.js build.

### 1. Railway — backend + data services

1. Create a project and add two plugins: **Postgres** and **Redis**.
2. Add your repo as a service (Railway auto-detects the `Dockerfile`).
3. Set the service variables (Variables tab → RAW editor). The app reads
   Railway's **native** `DATABASE_URL` / `REDIS_URL` directly, or the prefixed
   overrides — set whichever you prefer:

   ```bash
   # Data services — reference the plugins (names must match your services)
   HYBRIDRAG_DATABASE_URL=${{Postgres.DATABASE_URL}}
   HYBRIDRAG_REDIS_URL=${{Redis.REDIS_URL}}

   # Secrets / providers
   HYBRIDRAG_JWT_SECRET=<a long random secret>
   HYBRIDRAG_GROQ_API_KEY=<groq key>

   # Chroma Cloud (dense index)
   HYBRIDRAG_CHROMA_CLOUD=true
   HYBRIDRAG_CHROMA_API_KEY=<key>
   HYBRIDRAG_CHROMA_TENANT=<tenant-uuid>
   HYBRIDRAG_CHROMA_DATABASE=securecorp
   HYBRIDRAG_CHROMA_SERVER_URL=api.trychroma.com

   # Split-domain auth cookie (frontend and API are on different origins)
   HYBRIDRAG_CORS_ORIGINS=["https://<your-app>.vercel.app"]
   HYBRIDRAG_AUTH_COOKIE_DOMAIN=
   HYBRIDRAG_AUTH_COOKIE_SAMESITE=none
   HYBRIDRAG_AUTH_COOKIE_SECURE=true
   ```

   > The `preDeployCommand` (`python scripts/seed_db.py`) creates the schema and
   > seeds synthetic records on each deploy — idempotent (`IF NOT EXISTS` +
   > `ON CONFLICT DO NOTHING`). If Postgres isn't wired yet it logs a warning and
   > **skips** (exit 0) so the deploy still succeeds in document-RAG-only mode.

### 2. Vercel — frontend

1. Import the repo, set the project **root directory** to `web/`.
2. Set the production env var so the browser calls your Railway API:

   ```bash
   NEXT_PUBLIC_API_BASE=https://<your-backend>.up.railway.app
   ```

   > `NEXT_PUBLIC_*` is inlined at **build time**, so a change requires a
   > redeploy — not just a restart.

### 3. Verify

```bash
curl https://<your-backend>.up.railway.app/api/health
# {"status":"ok","retriever_wired":true,"redis_ok":true,"database_ok":true}
```

Then open the Vercel URL, log in with a demo user, and run a query — the
cross-site session cookie is sent because the API sets `SameSite=None; Secure`.

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.

---

## 📬 Contact

- **Project:** SecureCorp AI — HybridRAG + Reranking
- **Repository:** `securecorp-ai-hybridrag`
- **Purpose:** Enterprise GenAI/RAG portfolio project

---

---

<div align="center">
