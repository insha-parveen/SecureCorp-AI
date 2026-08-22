"""One-off: sweep the RRF k constant on the answerable dev subset.

Pure retrieval (no LLM) — tests whether the default rrf_k=60 is diluting
each retriever's high-confidence top hit. Reuses the loaded BM25 + dense
models across all k values. Reports Recall@5 / MRR / nDCG@5 / Hit@1 per k,
alongside the Dense-only and BM25-only baselines for reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import RankedChunk
from hybridrag.evaluation.retrieval_eval import RetrievalEvaluator
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse

USER = UserContext(user_id="sweep", roles=("admin",), department="HR", tenant_id="nexacore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ks", type=int, nargs="+", default=[5, 10, 20, 30, 60])
    args = parser.parse_args()

    cfg = get_settings()
    evaluator = RetrievalEvaluator(args.queries, settings=cfg)
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    embeddings = get_embedding_provider(cfg)
    embeddings.embed_query("warmup")

    def dense(q: str, _user: UserContext) -> list[RankedChunk]:
        return [
            RankedChunk(chunk=chunk, score=res.distance, rank=r, retriever="dense")
            for r, res in enumerate(
                store.query(embeddings.embed_query(q), top_k=cfg.dense_top_n), start=1
            )
            if (chunk := bm25.get(res.id)) is not None
        ]

    def bm25_fn(q: str, user: UserContext) -> list[RankedChunk]:
        return bm25.search(q, user_context=user, top_n=cfg.bm25_top_n)

    rows = []
    # baselines
    for name, fn in (("Dense-Only", dense), ("BM25-Only", bm25_fn)):
        m = evaluator.evaluate(fn, name)
        rows.append(
            {
                "arm": name,
                "recall_at_5": m.recall_at_k,
                "mrr": m.mrr,
                "ndcg_at_5": m.ndcg_at_k,
                "hit_at_1": m.hit_at_1,
            }
        )
        print(f"{name:<16} R@5={m.recall_at_k:.4f} MRR={m.mrr:.4f} hit@1={m.hit_at_1:.4f}")

    # RRF sweep
    for k in args.ks:

        def fused(q: str, user: UserContext, _k: int = k) -> list[RankedChunk]:
            return rrf_fuse(bm25_fn(q, user), dense(q, user), k=_k)

        m = evaluator.evaluate(fused, f"RRF(k={k})")
        rows.append(
            {
                "arm": f"RRF(k={k})",
                "k": k,
                "recall_at_5": m.recall_at_k,
                "mrr": m.mrr,
                "ndcg_at_5": m.ndcg_at_k,
                "hit_at_1": m.hit_at_1,
            }
        )
        print(f"RRF(k={k:<3}) R@5={m.recall_at_k:.4f} MRR={m.mrr:.4f} hit@1={m.hit_at_1:.4f}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"queries_path": str(args.queries), "rows": rows}, indent=2), encoding="utf-8"
    )
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
