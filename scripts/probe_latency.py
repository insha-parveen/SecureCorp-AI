"""Per-stage retrieval latency probe.

Measures wall-clock for each stage of the hybrid pipeline separately, over a
sample of real queries, with models pre-warmed. Reports p50/p95 per stage so
we can see exactly where the time goes (prime suspect: cross-encoder rerank).
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
from hybridrag.evaluation.retrieval_eval import _load_queries
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.reranker import CrossEncoderReranker

USER = UserContext(user_id="lat", roles=("admin",), department="HR", tenant_id="nexacore")


def _pct(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = int(round((p / 100) * (len(xs) - 1)))
    return xs[k]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    cfg = get_settings()
    rows = _load_queries(args.queries)
    queries = [r["query"] for r in rows][: args.n]

    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    embeddings = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)
    # Warm up (exclude cold model-load cost from the per-query numbers)
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])

    t: dict[str, list[float]] = {
        "bm25": [],
        "embed": [],
        "dense_query": [],
        "rrf": [],
        "rerank": [],
        "end_to_end_no_rerank": [],
        "end_to_end_with_rerank": [],
    }

    for q in queries:
        e2e0 = time.perf_counter()

        t0 = time.perf_counter()
        bm25_res = bm25.search(q, user_context=USER, top_n=cfg.bm25_top_n)
        t["bm25"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        emb = embeddings.embed_query(q)
        t["embed"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        matches = store.query(emb, top_k=cfg.dense_top_n)
        t["dense_query"].append((time.perf_counter() - t0) * 1000)
        dense_res = [
            RankedChunk(chunk=c, score=m.distance, rank=r, retriever="dense")
            for r, m in enumerate(matches, start=1)
            if (c := bm25.get(m.id)) is not None
        ]

        t0 = time.perf_counter()
        fused = rrf_fuse(bm25_res, dense_res)
        t["rrf"].append((time.perf_counter() - t0) * 1000)

        # end-to-end WITHOUT rerank = time so far
        t["end_to_end_no_rerank"].append((time.perf_counter() - e2e0) * 1000)

        t0 = time.perf_counter()
        _ = reranker.rerank(q, fused[: cfg.rerank_candidates])[: cfg.final_top_k]
        t["rerank"].append((time.perf_counter() - t0) * 1000)

        t["end_to_end_with_rerank"].append((time.perf_counter() - e2e0) * 1000)

    report = {
        "n_queries": len(queries),
        "rerank_candidates": cfg.rerank_candidates,
        "reranker_model": cfg.reranker_model,
        "embedding_model": cfg.embedding_model,
        "stages_ms": {
            stage: {
                "mean": round(statistics.mean(v), 1),
                "p50": round(_pct(v, 50), 1),
                "p95": round(_pct(v, 95), 1),
                "max": round(max(v), 1),
            }
            for stage, v in t.items()
            if v
        },
    }
    print(json.dumps(report, indent=2))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
