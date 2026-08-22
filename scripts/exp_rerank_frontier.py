"""Rerank candidate-count frontier: quality AND latency vs rerank_candidates.

At the tuned fusion k=10, sweep rerank_candidates to find the knee — the
point where recall plateaus so we don't pay reranker latency for candidates
that never change the top-5. Reports Recall@5/MRR/Hit@1 and measured mean
rerank latency per candidate count.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import RankedChunk
from hybridrag.evaluation.retrieval_eval import RetrievalEvaluator, _load_queries
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.reranker import CrossEncoderReranker

USER = UserContext(user_id="frontier", roles=("admin",), department="HR", tenant_id="nexacore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--k", type=int, default=10, help="RRF k for fusion.")
    parser.add_argument("--cands", type=int, nargs="+", default=[0, 10, 15, 20, 30, 50])
    args = parser.parse_args()

    cfg = get_settings()
    ev = RetrievalEvaluator(args.queries, settings=cfg)
    rows_q = _load_queries(args.queries)
    queries = [r["query"] for r in rows_q]
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    emb = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)
    emb.embed_query("warmup")
    reranker.rerank("warmup", [])

    def dense(q: str, _u: UserContext) -> list[RankedChunk]:
        return [
            RankedChunk(chunk=c, score=m.distance, rank=r, retriever="dense")
            for r, m in enumerate(store.query(emb.embed_query(q), top_k=cfg.dense_top_n), start=1)
            if (c := bm25.get(m.id)) is not None
        ]

    def fused(q: str, u: UserContext) -> list[RankedChunk]:
        return rrf_fuse(bm25.search(q, user_context=u, top_n=cfg.bm25_top_n), dense(q, u), k=args.k)

    rows = []
    for cand in args.cands:
        if cand == 0:
            fn = lambda q, u: fused(q, u)[: cfg.final_top_k]  # noqa: E731
            label = f"k={args.k}_norerank"
        else:

            def fn(q: str, u: UserContext, _c: int = cand) -> list[RankedChunk]:
                return reranker.rerank(q, fused(q, u)[:_c])[: cfg.final_top_k]

            label = f"k={args.k}_rerank_c{cand}"

        m = ev.evaluate(fn, label)

        # measure latency of just this arm's retrieval over the query set
        lat = []
        for q in queries:
            t0 = time.perf_counter()
            fn(q, USER)
            lat.append((time.perf_counter() - t0) * 1000)

        rows.append(
            {
                "arm": label,
                "rerank_candidates": cand,
                "recall_at_5": round(m.recall_at_k, 4),
                "mrr": round(m.mrr, 4),
                "hit_at_1": round(m.hit_at_1, 4),
                "latency_ms_mean": round(statistics.mean(lat), 1),
                "latency_ms_p95": round(sorted(lat)[int(0.95 * (len(lat) - 1))], 1),
            }
        )
        print(
            f"{label:<22} R@5={m.recall_at_k:.4f} hit@1={m.hit_at_1:.4f} "
            f"lat_mean={rows[-1]['latency_ms_mean']}ms p95={rows[-1]['latency_ms_p95']}ms"
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"queries_path": str(args.queries), "k": args.k, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
