# SecureCorp AI — HybridRAG + Reranking

### Project Documentation & Presentation Brief

> A secure, evaluation-driven enterprise knowledge assistant that answers
> questions over heterogeneous company documents **and** structured business
> records — with authorization enforced *before* any evidence reaches the LLM.

---

## 1. Executive Summary

**SecureCorp AI** is an advanced Retrieval-Augmented Generation (RAG) system built
for a fictional enterprise, **NexaCore Solutions Pvt. Ltd.** It goes well beyond the
"documents → embeddings → vector search → LLM" baseline that most RAG demos stop at.

It combines **hybrid retrieval** (keyword + semantic), **cross-encoder reranking**,
**role- and attribute-based access control**, **authorization-aware caching**,
**structured SQL retrieval**, and **server-side citation validation** into one
coherent, tested, and measurable pipeline.

The guiding principle is **trustworthy retrieval**: the system should retrieve the
*right* evidence, prove the user is *allowed* to see it, and answer *only* from
evidence it can cite — or abstain.

|                           |                                                              |
| ------------------------- | ------------------------------------------------------------ |
| **Domain**          | Enterprise knowledge assistant (synthetic corpus)            |
| **Retrieval**       | Hybrid: BM25 + dense → RRF → cross-encoder rerank          |
| **Vector store**    | Chroma Cloud (behind a provider-agnostic adapter)            |
| **Backend**         | FastAPI (Python 3.11), streaming SSE chat                    |
| **Frontend**        | Next.js 15 (App Router), Tailwind, TanStack Query            |
| **Structured data** | PostgreSQL via template-based SQL (no free-form text-to-SQL) |
| **Cache**           | Redis — L1 exact + L2 semantic, scope-hashed keys           |
| **LLM**             | Groq (hosted) / Ollama (local), model is configurable        |

---

## 2. Problem Statement

Most introductory RAG systems follow a single, naive path:

```
documents → chunks → embeddings → vector search → LLM
```

For a real **enterprise** knowledge assistant this is insufficient and, worse,
**unsafe**. Concretely, the naive approach fails on eight fronts:

1. **Keyword blindness.** Pure semantic search misses exact identifiers —
   invoice numbers, employee IDs, policy codes, product SKUs (`INV-2026-0108`,
   `EMP-0104`, `INC-1042`).
2. **Semantic blindness.** Pure keyword search misses paraphrases and conceptual
   questions.
3. **No access control.** Vector search will happily retrieve a confidential HR
   document for any user who asks.
4. **Client-trusted identity.** Naive systems trust a `role` or `user_id` sent in
   the request body — trivially forgeable.
5. **Wasted inference.** Repeated questions re-run the full (expensive) LLM path.
6. **Wrong tool for structured data.** "What is the total of invoice X?" is a SQL
   lookup, not a similarity search — forcing it through embeddings gives fuzzy,
   unreliable answers.
7. **Fabricated citations.** LLMs invent plausible-looking but non-existent
   sources.
8. **Unmeasured quality.** Changes to chunking, retrieval, or prompts ship without
   any evidence they helped — or that they didn't regress.

### The core question this project answers

> *How do you build a RAG system that an enterprise could actually trust — one
> that retrieves the right evidence, enforces who is allowed to see it, never
> fabricates a citation, and can prove its own quality with reproducible metrics?*

### SecureCorp AI's answer — the secure request pipeline

```
authentication → authorization → secure cache → query routing
   → hybrid search (BM25 + dense) or authorized SQL
   → RRF → cross-encoder reranking → evidence validation
   → LLM generation → citation validation → response → cache
```

Authorization is applied **before** retrieval, so unauthorized content is never
even a candidate — not retrieved-then-filtered. The LLM is never allowed to decide
whether a user is authorized, and may only cite evidence IDs the application
supplied.

---

## 3. The Enterprise Scenario (Synthetic)

Everything is **fictional and synthetic** — no real private data is ever used.

- **Company:** NexaCore Solutions Pvt. Ltd. — software consulting, cloud & managed IT
- **Size:** ~250 employees across Lucknow, Bengaluru, Dubai, Singapore
- **Departments:** HR, Engineering, Finance, Operations, Sales, IT & Security, Admin
- **Application roles:** `employee`, `manager`, `hr`, `finance`, `it`, `admin`
- **Document classifications:** `public`, `department_internal`, `restricted`, `confidential`

---

## 4. Key Capabilities

1. **Heterogeneous ingestion** — policies, knowledge-base articles, emails,
   meetings, Slack threads, Jira issues, GitHub items.
2. **Document-type-aware chunking** — a policy paragraph, an email, a meeting
   speaker-turn, and a Slack message are each chunked by their own rules, never
   one blind fixed-size splitter.
3. **Hybrid retrieval** — BM25 (exact/lexical) + dense semantic, fused via
   Reciprocal Rank Fusion on globally unique `chunk_id`.
4. **Cross-encoder reranking** — a second-stage model reorders a bounded
   candidate set for final precision.
5. **RBAC + ABAC authorization** — role checks *plus* attribute rules (ownership,
   department, manager scope, tenant).
6. **Authorization-aware caching** — L1 exact + L2 semantic, keyed by security
   scope so cache reuse can never cross an authorization boundary.
7. **Structured SQL path** — exact record lookups and aggregations go to
   PostgreSQL via safe, template-based queries.
8. **Citation-enforced generation** — every citation the LLM emits is validated
   server-side against real indexed evidence; unknown IDs are rejected.
9. **Abstention** — when evidence is insufficient, the system declines rather
   than fabricating.
10. **Offline evaluation harness** — retrieval metrics, RAGAS, citation/security
    /cache experiments, all reproducible and never tuned on the holdout set.

---

## 5. System Architecture

```
                              USER
                                │
                                ▼
                     Authentication (JWT)
                                │
                                ▼
             Authorization Context (roles, dept, tenant, scope)
                                │
                                ▼
              Authorization-Aware Cache  (L1 exact → L2 semantic)
                                │  (miss)
                                ▼
                        Query Classification
                 ┌──────────────┼──────────────┐
                 ▼              ▼               ▼
          DOCUMENT_RAG    STRUCTURED_SQL      REFUSE
                 │              │
                 ▼              ▼
       Authorization-aware   Authorized,
        Hybrid Retrieval     template SQL
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
  BM25 / sparse        Dense vector
  (exact/lexical)      (Chroma Cloud)
      └──────────┬──────────┘
                 ▼
       Reciprocal Rank Fusion (by unique chunk_id)
                 ▼
          Cross-Encoder Reranker
                 ▼
             Top-K Evidence
                 ▼
          Evidence Validation
                 ▼
          LLM Answer Generation
                 ▼
          Citation Validation  (reject unknown IDs)
                 ▼
            Secure Response  →  cached with scope hash
```

**Architecture invariants that are deliberately never broken** — RRF fuses on
`chunk_id` (never `document_id` alone); authorization runs before evidence reaches
the LLM; cached answers never cross authorization scopes; every citation resolves
to a real indexed chunk or record; RAGAS is offline only, never on the request path.

---

## 6. Retrieval Strategy (the technical heart)

For every document query: **authorize → BM25 over authorized chunks → dense search
(same auth filter) → RRF fusion → dedupe → cross-encoder rerank → top-K**, with the
full strategy metadata exposed for debugging and evaluation.

| Stage  | Choice                              | Why                                              |
| ------ | ----------------------------------- | ------------------------------------------------ |
| Sparse | BM25Okapi (k1=1.5, b=0.75)          | Catches exact IDs/codes dense retrieval misses   |
| Dense  | MiniLM (384-dim), cosine            | Semantic similarity & paraphrase                 |
| Fusion | RRF, k=60, on`chunk_id`           | Rank-based, scale-free combination of both lists |
| Rerank | cross-encoder/ms-marco-MiniLM-L6-v2 | Precision on a bounded candidate set             |

**A concrete illustration of *why* hybrid matters** — a diagnostic probe over the
40 identifiers that occur in exactly one chunk of the corpus:

```
BM25  hit@1: 40/40      ← exact identifiers
dense hit@1:  4/40      ← semantic model can't localize an ID
```

(This is a diagnostic that *justifies* the architecture; the formal quality numbers
come from the evaluation harness — see §9.)

---

## 7. Data Model & Corpus (As Built)

**Corpus (real, measured):**

```
Documents ingested : 275   (from 260 Markdown files)
Chunks produced    : 450
Body tokens        : 124,472  (exact, MiniLM tokenizer)
Chunk size         : min 67 · median 269 · max 440 tokens
```

Source families: policy, knowledge_base, email, meeting, slack, jira, github.
(Each Slack *thread* is its own document, independently authorized — which is why
275 documents come from 260 files.)

**Structured records (PostgreSQL):** `employees`, `invoices`, `expense_claims`,
`it_tickets`, each row carrying a `tenant_id`. Synthetic IDs (`EMP-0104`,
`INV-2026-0108`, `INC-1042`) are deliberately used in evaluation queries to test
exact-match retrieval.

**Every chunk carries provenance for secure filtering & citations:** `chunk_id`,
`document_id`, `document_version`, `text`, `section_title`, `token_count`,
`content_hash`, `document_type`, `department`, `classification`, `allowed_roles`,
`allowed_departments`, `tenant_id`, `effective_date`.

---

## 8. Security Model

The single most important invariant of the whole project:

> **Unauthorized chunks reaching the LLM context = 0.**

- **RBAC + ABAC** — roles plus attributes (ownership, department, manager scope,
  tenant). Enforced in application code and at the data-access boundary, *not* in
  prompts.
- **Server-trusted identity** — the authorization context comes from a validated
  JWT, never from the client request body.
- **No information leakage** — authorization-denial messages must not reveal that a
  sensitive document exists.
- **Cache isolation** — cache keys embed an authorization-scope hash, so no answer
  is ever reused across roles/departments/tenants.
- **Citation integrity** — the LLM may cite only application-supplied evidence IDs;
  every returned ID is validated server-side and unknown IDs are rejected.

Security is tested as a first-class concern: unauthorized retrieval, cross-user /
cross-role cache leakage, ownership violations, prompt injection, and citation
tampering.

---

## 9. Evaluation Strategy

Evaluation is **offline** and reproducible — never part of the live request path,
and **never tuned on the holdout set** (`development.jsonl` = 283 items for tuning,
`holdout.jsonl` = 71 items for final reporting).

- **Retrieval metrics** (per strategy: Dense-only, BM25-only, Hybrid RRF, Hybrid +
  Rerank): Recall@5/@10, Hit@5, MRR@10, nDCG@10.
- **Generation (RAGAS):** faithfulness, answer relevancy, context precision/recall.
- **Citation metrics:** validity, unsupported-citation rate, coverage, invalid-ID rate.
- **Security metrics:** the zero-leakage invariant, plus the attack cases above.
- **Operational metrics:** p50/p95 latency, per-stage latency, cache hit rate, LLM
  calls avoided.

> **Integrity note (important for the presentation):** this project deliberately
> ships with metrics marked *"measured"* rather than pre-filled numbers. Every value
> in the final report comes from an actual run of the evaluation harness — no
> invented benchmarks. This is a stated, enforced project rule.

---

## 10. Technology Stack

| Layer               | Technology                                                      |
| ------------------- | --------------------------------------------------------------- |
| Language / tooling  | Python 3.11,`uv`, `ruff`, `mypy`                          |
| Backend             | FastAPI, streaming SSE, JWT auth                                |
| Frontend            | Next.js 15 (App Router), Tailwind v4, shadcn/ui, TanStack Query |
| Vector store        | Chroma Cloud (behind a`VectorStore` adapter interface)        |
| Sparse retrieval    | `rank-bm25`                                                   |
| Embeddings / rerank | sentence-transformers (MiniLM), cross-encoder                   |
| Structured data     | PostgreSQL via`psycopg[binary]`                               |
| Cache               | Redis (L1 exact + L2 semantic)                                  |
| LLM providers       | Groq (hosted) / Ollama (local) — pluggable                     |
| Evaluation          | RAGAS + deterministic retrieval metrics                         |
| Deployment          | Backend on Railway (Docker), frontend on Vercel                 |

**Engineering discipline:** `src/` layout, domain models kept independent of
Chroma/BM25/FastAPI, provider adapters for model backends, no hardcoded secrets, all
model names and retrieval params driven by configuration.

---

## 12. What Makes This Project Stand Out

If you present one slide, make it this one:

1. **Security-first RAG** — authorization *before* retrieval, with a hard,
   testable zero-leakage invariant. Most RAG demos have no access control at all.
2. **Genuinely hybrid** — BM25 + dense + RRF + cross-encoder, with a diagnostic
   that *proves* why (40/40 vs 4/40 on exact identifiers).
3. **Right tool for the data** — structured questions route to safe template SQL,
   not forced through embeddings.
4. **Anti-hallucination by construction** — server-side citation validation and
   principled abstention.
5. **Evaluation-driven & honest** — reproducible metrics on a held-out set, with an
   explicit rule against inventing numbers.
6. **Production-shaped** — streaming API, scope-aware caching, config-driven,
   containerized, split-domain cloud deployment.
