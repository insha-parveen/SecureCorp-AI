# SecureCorp AI — HybridRAG + Reranking

### Project Documentation & Presentation Brief

> A secure, evaluation-driven enterprise knowledge assistant that answers
> questions over heterogeneous company documents **and** structured business
> records — with authorization enforced _before_ any evidence reaches the LLM.

## 1. Executive Summary

**SecureCorp AI** is an advanced Retrieval-Augmented Generation (RAG) system built
for a fictional enterprise, **NexaCore Solutions Pvt. Ltd.** It goes well beyond the
"documents → embeddings → vector search → LLM" baseline that most RAG demos stop at.

It combines **hybrid retrieval** (keyword + semantic), **cross-encoder reranking**,
**role- and attribute-based access control**, **authorization-aware caching**,
**structured SQL retrieval**, and **server-side citation validation** into one
coherent, tested, and measurable pipeline.

The guiding principle is **trustworthy retrieval**: the system should retrieve the
_right_ evidence, prove the user is _allowed_ to see it, and answer _only_ from
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

> _How do you build a RAG system that an enterprise could actually trust — one
> that retrieves the right evidence, enforces who is allowed to see it, never
> fabricates a citation, and can prove its own quality with reproducible metrics?_

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
5. **RBAC + ABAC authorization** — role checks _plus_ attribute rules (ownership,
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
| Fusion | RRF, k=10, on `chunk_id`            | Rank-based, scale-free combination of both lists |
| Rerank | cross-encoder/ms-marco-MiniLM-L6-v2 | Precision on a bounded candidate set             |

Two tuning decisions matter and are backed by measurement, not defaults:

- **RRF `k=10`, not the library default 60.** At `k=60` the `1/(k+rank)` weights
  flatten so much that fusion scored _below_ its own inputs; `k=10` restores
  fusion's top-rank advantage so Hybrid beats both Dense and BM25.
- **Reranker is skipped for exact-identifier queries.** The cross-encoder ranks
  semantic prose above the chunk that literally contains an ID like `ITSEC-002`
  — measured as exact-identifier Recall@5 collapsing from 100% to 0%. A
  structural identifier check (shared with the BM25 tokenizer) bypasses the
  reranker for those queries, recovering them to 100% and saving ~1 s of latency.

## 7. Data Model & Corpus (As Built)

**Corpus (real, measured):**

```
Documents ingested : 276   (from 260 Markdown files)
Chunks produced    : 455
Body tokens        : 125,813  (exact, MiniLM tokenizer)
Chunk size         : min 67 · median 269 · max 440 tokens
```

Source families: policy, knowledge*base, email, meeting, slack, jira, github.
(Each Slack \_thread* is its own document, independently authorized — which is why
276 documents come from 260 files.)

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
  tenant). Enforced in application code and at the data-access boundary, _not_ in
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
and **never tuned on the holdout set**. The golden set is split
`development.jsonl` (343 items, for tuning) and `holdout.jsonl` (71 items, for
final reporting). The dev split was expanded (see §11) so the thin categories
carry enough samples to be trustworthy rather than coin-flips.

- **Retrieval metrics** (per strategy: Dense-only, BM25-only, Hybrid RRF, Hybrid +
  Rerank): Recall@5/@10, Hit@1, MRR@10, nDCG@10.
- **Generation (RAGAS):** faithfulness, answer relevancy, context precision/recall.
- **Citation metrics:** validity, unsupported-citation rate, coverage, invalid-ID rate.
- **Security metrics:** the zero-leakage invariant, plus the attack cases above.
- **Abstention / refusal:** fraction of unanswerable questions correctly declined
  and prompt-injection attempts correctly refused.
- **Operational metrics:** p50/p95 latency, per-stage latency, cache hit rate, LLM
  calls avoided.

**How the eval measures retrieval, not clearance.** A single fixed eval identity
made every document that identity could not read score as a retrieval _miss_,
conflating "retrieval failed" with "authorization correctly refused" — an
artificial ~10-point ceiling on every arm. The harness now assigns each golden
query an identity actually authorized for its expected documents (derived from
the row's own `expected_roles` and what those documents grant). Authorization is
**not** weakened: `is_authorized` still runs on every retrieved chunk; we simply
stop penalizing retrieval for the arbitrary eval user's missing clearance. A
`residual_auth_ceiling()` reporter makes the remaining, unavoidable ceiling
explicit (a user has one department, so a query whose expected docs span
departments can never be fully reached).

> **Integrity note (important for the presentation):** every value in §10 comes
> from an actual run of the evaluation harness — no invented benchmarks. This is
> a stated, enforced project rule, guarded in code (the landing page has a unit
> test that fails if an unmeasured metric is smuggled in).

---

## 10. Measured Results

All figures below are real harness output, authorization enforced (the
production path), with RRF `k=10` and the identifier-aware reranker bypass live.

**Retrieval ablation — 80-query legacy set:**

| Strategy        | Recall@5   | Hit@1  | MRR@10 | nDCG@10 |
| --------------- | ---------- | ------ | ------ | ------- |
| Dense-only      | 85.00%     | 51.25% | 0.663  | 0.953   |
| BM25-only       | 92.50%     | 60.00% | 0.736  | 1.068   |
| **Hybrid (RRF)**| **95.00%** | 56.25% | 0.723  | 1.073   |
| Hybrid + Rerank | 88.75%     | 56.25% | 0.707  | 0.929   |

**Retrieval ablation — 64-item answerable holdout (final reporting split):**

| Strategy        | Recall@5   | Hit@1  | MRR@10 | nDCG@10 |
| --------------- | ---------- | ------ | ------ | ------- |
| Dense-only      | 84.38%     | 39.06% | 0.595  | 1.031   |
| BM25-only       | 85.94%     | 59.38% | 0.726  | 1.209   |
| **Hybrid (RRF)**| **90.62%** | 46.88% | 0.664  | 1.188   |
| Hybrid + Rerank | 87.50%     | 53.12% | 0.672  | 0.991   |

Against a **measured achievable ceiling of 96.25%** on the 80q set (3 of 80 rows
cite documents no single-department identity can see), Hybrid-RRF at 95.00% is
essentially at the ceiling. Best all-round arm is **Hybrid-RRF**; the reranker
trades a little top-5 recall for stronger top-1 on some categories, which is why
it stays available but is bypassed for exact-identifier lookups.

**Abstention & refusal (expanded golden set, gpt-oss judge):**

| Case                       | Correct decline |
| -------------------------- | --------------- |
| Unanswerable questions     | 16 / 16 = 100%  |
| Prompt-injection attempts  | 6 / 6 = 100%    |

(An earlier "0.50" was a measurement artifact: three code paths each carried a
_different_ abstention phrase list, so a correct decline phrased a fourth way was
scored as a failure. All three now share one canonical sentence + one detector.)

**Citations (n=32 subset):** valid 100% · invalid-ID rate 0% · coverage 95.7%.

**Security:** zero unauthorized chunks reached the LLM across the suite; cache
isolation shows 0 cross-tenant / cross-role / cross-department reuse. Both are
guarded by regression tests.

**Latency:** the cross-encoder reranker dominates retrieval latency (~1 s);
everything else (BM25, embed, dense, RRF) is tens of milliseconds. The
identifier bypass removes that ~1 s on exact-ID lookups.

---

## 11. Golden-Set Expansion (Evaluation Rigor)

Some evaluation categories were originally too small to trust — a single
mis-scored query could swing them wildly. The dev split was expanded with **60
new hand-authored, corpus-grounded queries** (every one cites a real
`document_id`, with `expected_roles` filled from that document's actual
metadata by a validator that aborts on any mismatch):

| Category            | Before | After |
| ------------------- | ------ | ----- |
| semantic_paraphrase | 17     | 33    |
| exact_identifier    | 8      | 24    |
| prompt_injection    | 6      | 20    |
| unanswerable        | 2      | 16    |

This immediately corrected a false alarm: `semantic_paraphrase` had read **25%
(n=4)** and looked like a dense-retrieval weakness; on the meaningful **n=33 it
is 93.94%**. The "problem" was sampling noise, not the retriever — so a planned
embedding-model swap was correctly _cancelled_ rather than chased.

---

## 12. Technology Stack

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

## 13. What Makes This Project Stand Out

If you present one slide, make it this one:

1. **Security-first RAG** — authorization _before_ retrieval, with a hard,
   testable zero-leakage invariant. Most RAG demos have no access control at all.
2. **Genuinely hybrid** — BM25 + dense + RRF + cross-encoder, with a diagnostic
   that _proves_ why (40/40 vs 4/40 on exact identifiers), reaching **95% Recall@5**.
3. **Right tool for the data** — structured questions route to safe template SQL,
   not forced through embeddings.
4. **Anti-hallucination by construction** — server-side citation validation and
   principled abstention (100% correct decline on unanswerable & injection cases).
5. **Evaluation-driven & honest** — reproducible metrics on a held-out set, with an
   explicit rule against inventing numbers, and eval methodology that measures
   retrieval rather than the eval user's clearance.
6. **Production-shaped** — streaming API, scope-aware caching, config-driven,
   containerized, split-domain cloud deployment.

---

## 14. Key Findings (measured this cycle)

Each of these is a real, quantified result — several corrected an earlier wrong
conclusion, which is the point: the eval harness caught them.

1. **The vector-store pre-filter was destroying recall.** An overly restrictive
   Chroma `where`-clause eliminated legitimately authorized documents _before_
   retrieval (it omitted role-based grants). Replacing it with over-fetch +
   authoritative `is_authorized` post-filtering lifted **Dense Recall@5 30% →
   76%** and **Hybrid-RRF 64% → 85%** at ~11 ms cost, with **no change to the
   authorization boundary** (proven by a regression test).

2. **RRF `k=60` made fusion worse than its inputs.** Retuning to **`k=10`**
   restored fusion's advantage so Hybrid beats both Dense and BM25.

3. **The reranker silently killed exact-identifier retrieval** (Recall@5 100% →
   0%): it ranks semantic prose above the chunk that literally contains the ID.
   An identifier-aware **bypass** restores it to 100% _and_ removes ~1 s latency
   on those queries.

4. **The eval harness was scoring authorization as retrieval failure.** Giving
   each query an authorized identity (without weakening the auth check) removed a
   ~10-point artificial ceiling, revealing the true **95% Hybrid-RRF Recall@5**.

5. **`semantic_paraphrase` was never weak** — the alarming "25%" was 1 of 4
   queries. On n=33 it is **93.94%**; a planned embedding swap was cancelled.

6. **Abstention "0.50" was a measurement bug**, not behaviour — three divergent
   phrase lists. Unified to one detector; measured **100%** correct decline on
   unanswerable and prompt-injection cases.

> **Headline for the presentation:**
> _"Most of our biggest 'improvements' were really measurement fixes. By making
> the evaluation honest — measuring retrieval instead of the test user's
> clearance, and using statistically meaningful sample sizes — we took Hybrid
> Recall@5 to 95%, proved the reranker was hurting identifier lookups, and showed
> abstention was already at 100%. Every number is reproducible from the harness."_
