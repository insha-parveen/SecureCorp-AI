"""Head-to-head retrieval improvement experiment on the legacy 80-query set.

Compares configurations that address the two findings (reranker not helping,
latency too high) with real Recall@5 / MRR / Hit@1 numbers:

  A. Dense-only                       (baseline, no BM25, no rerank)
  B. BM25-only
  C. Hybrid RRF k=60                  (current default)
  D. Hybrid RRF k=10                  (tuned fusion, NO reranker)
  E. Hybrid RRF k=10 + rerank(cand=30) (tuned fusion + current reranker)
  F. Hybrid RRF k=10 + rerank(cand=50) (wider candidate pool for the reranker)

All arms reuse one set of pre-warmed models. Pure retrieval, no LLM.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import RankedChunk
from hybridrag.evaluation.retrieval_eval import RetrievalEvaluator
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.reranker import CrossEncoderReranker

USER = UserContext(user_id="exp", roles=("admin",), department="HR", tenant_id="nexacore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    cfg = get_settings()
    ev = RetrievalEvaluator(args.queries, settings=cfg)
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

    def bm(q: str, u: UserContext) -> list[RankedChunk]:
        return bm25.search(q, user_context=u, top_n=cfg.bm25_top_n)

    def hybrid(q: str, u: UserContext, k: int) -> list[RankedChunk]:
        return rrf_fuse(bm(q, u), dense(q, u), k=k)

    def hybrid_rerank(q: str, u: UserContext, k: int, cand: int) -> list[RankedChunk]:
        fused = hybrid(q, u, k)
        return reranker.rerank(q, fused[:cand])[: cfg.final_top_k]

    arms: dict[str, Callable[[str, UserContext], list[RankedChunk]]] = {
        "A_dense_only": dense,
        "B_bm25_only": bm,
        "C_hybrid_k60_norerank": lambda q, u: hybrid(q, u, 60),
        "D_hybrid_k10_norerank": lambda q, u: hybrid(q, u, 10),
        "E_hybrid_k10_rerank_c30": lambda q, u: hybrid_rerank(q, u, 10, 30),
        "F_hybrid_k10_rerank_c50": lambda q, u: hybrid_rerank(q, u, 10, 50),
    }

    rows = []
    for name, fn in arms.items():
        m = ev.evaluate(fn, name)
        rows.append(
            {
                "arm": name,
                "recall_at_5": round(m.recall_at_k, 4),
                "mrr": round(m.mrr, 4),
                "hit_at_1": round(m.hit_at_1, 4),
                "ndcg_at_5": round(m.ndcg_at_k, 4),
            }
        )
        print(
            f"{name:<26} R@5={m.recall_at_k:.4f}  MRR={m.mrr:.4f}  "
            f"hit@1={m.hit_at_1:.4f}  nDCG@5={m.ndcg_at_k:.4f}"
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"queries_path": str(args.queries), "rows": rows}, indent=2), encoding="utf-8"
    )
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
