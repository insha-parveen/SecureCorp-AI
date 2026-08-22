"""Isolate WHY the ablation Hybrid-Rerank (80%) != inline rerank frontier (90%).

Both use k=10 fusion + ms-marco rerank c15 -> top-5 on the SAME 80q set, yet the
ablation arm (production `hybrid.retrieve`) scores lower. Hypothesis: the only
difference is that `hybrid.retrieve` applies the authorization `where` filter to
the dense pool + post-filters by `is_authorized`, while the frontier/inline path
queries dense UNfiltered. This probe runs three arms in one process to confirm:

  A = production hybrid.retrieve            (auth-filtered dense)   -> expect ~80%
  B = inline rerank, UNfiltered dense       (what the frontier did) -> expect ~90%
  C = inline rerank, AUTH-filtered dense    (isolates the filter)   -> should match A

If C == A and B is higher, the gap is the authorization filter, not a rerank bug.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybridrag.authorization.engine import AuthorizationEngine
from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import RankedChunk
from hybridrag.evaluation.retrieval_eval import _load_queries
from hybridrag.indexing import BM25Index, ChromaVectorStore, decode_chunk, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker, rerank_top

USER = UserContext(user_id="eval", roles=("admin",), department="HR", tenant_id="nexacore")


def _recall_hit1(rows, retrieve, k=5) -> tuple[float, float, int]:
    hits = 0
    hit1 = 0
    n = 0
    for r in rows:
        exp = set(r.get("expected_chunk_sources", r.get("expected_documents", [])))
        exp = {d for d in exp if d and d != "*"}
        if not exp:
            continue
        n += 1
        res = retrieve(r["query"])
        first = 0
        for rank, rc in enumerate(res, start=1):
            if rc.chunk.document_id in exp:
                first = rank
                break
        if first and first <= k:
            hits += 1
        if first == 1:
            hit1 += 1
    return (round(hits / n, 4), round(hit1 / n, 4), n)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queries", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    cfg = get_settings()
    rows = _load_queries(args.queries)
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    emb = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)
    emb.embed_query("warmup")
    reranker.rerank("warmup", [])
    hybrid = HybridRetriever(bm25, store, emb, reranker, settings=cfg)

    def dense_unfiltered(q: str) -> list[RankedChunk]:
        return [
            RankedChunk(chunk=c, score=m.distance, rank=r, retriever="dense")
            for r, m in enumerate(store.query(emb.embed_query(q), top_k=cfg.dense_top_n), start=1)
            if (c := bm25.get(m.id)) is not None
        ]

    def dense_authfiltered(q: str) -> list[RankedChunk]:
        where = AuthorizationEngine.build_dense_filter(USER)
        out: list[RankedChunk] = []
        for r, m in enumerate(
            store.query(emb.embed_query(q), top_k=cfg.dense_top_n, where=where), start=1
        ):
            c = decode_chunk(m.text, m.metadata)
            if AuthorizationEngine.is_authorized(USER, c):
                out.append(RankedChunk(chunk=c, score=float(m.distance), rank=r, retriever="dense"))
        return out

    def arm_A(q: str) -> list[RankedChunk]:  # production
        return hybrid.retrieve(q, user_context=USER)

    def arm_B(q: str) -> list[RankedChunk]:  # inline, unfiltered dense
        fused = rrf_fuse(
            bm25.search(q, user_context=USER, top_n=cfg.bm25_top_n), dense_unfiltered(q)
        )
        return rerank_top(
            q,
            fused,
            reranker=reranker,
            rerank_candidates=cfg.rerank_candidates,
            final_top_k=cfg.final_top_k,
        )

    def arm_C(q: str) -> list[RankedChunk]:  # inline, auth-filtered dense
        fused = rrf_fuse(
            bm25.search(q, user_context=USER, top_n=cfg.bm25_top_n), dense_authfiltered(q)
        )
        return rerank_top(
            q,
            fused,
            reranker=reranker,
            rerank_candidates=cfg.rerank_candidates,
            final_top_k=cfg.final_top_k,
        )

    out = {"config": {"rrf_k": cfg.rrf_k, "rerank_candidates": cfg.rerank_candidates}, "arms": {}}
    for name, fn in [
        ("A_production_hybrid_retrieve", arm_A),
        ("B_inline_dense_UNfiltered", arm_B),
        ("C_inline_dense_authfiltered", arm_C),
    ]:
        r5, h1, n = _recall_hit1(rows, fn)
        out["arms"][name] = {"recall_at_5": r5, "hit_at_1": h1, "n": n}
        print(f"{name:32s} recall@5={r5}  hit@1={h1}  n={n}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
