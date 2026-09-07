"""Diagnose retrieval misses at the best config (k=10 fusion + rerank).

For every query where the expected doc is NOT in the final top-5, report where
that doc actually sits: its rank in BM25, in dense, in the fused list, and in
the reranked list. This separates two very different failure modes:

  * "mis-ranked" — the doc IS retrieved (in top-50 fused) but rerank/fusion
    pushed it below 5. Fixable by better ordering.
  * "not retrieved" — the doc never appears in top-50 of either retriever.
    Needs deeper retrieval / query expansion / better embeddings.

Also reports, for HITS, the final rank, to see the Hit@1 gap (docs ranked 2-5).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import RankedChunk
from hybridrag.evaluation.retrieval_eval import _load_queries
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.fusion import rrf_fuse
from hybridrag.retrieval.reranker import CrossEncoderReranker

USER = UserContext(user_id="diag", roles=("admin",), department="HR", tenant_id="nexacore")


def _rank_of(expected: set[str], ranked: list[RankedChunk]) -> int:
    for i, rc in enumerate(ranked, start=1):
        if rc.chunk.document_id in expected:
            return i
    return 0  # 0 == not present


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--cand", type=int, default=15)
    args = parser.parse_args()

    cfg = get_settings()
    rows = _load_queries(args.queries)
    bm25 = BM25Index.from_chunk_file(cfg.processed_dir / "chunks.jsonl", settings=cfg)
    store = ChromaVectorStore.from_settings(cfg)
    emb = get_embedding_provider(cfg)
    reranker = CrossEncoderReranker.from_settings(cfg)
    emb.embed_query("warmup")
    reranker.rerank("warmup", [])

    def dense(q: str) -> list[RankedChunk]:
        return [
            RankedChunk(chunk=c, score=m.distance, rank=r, retriever="dense")
            for r, m in enumerate(store.query(emb.embed_query(q), top_k=cfg.dense_top_n), start=1)
            if (c := bm25.get(m.id)) is not None
        ]

    misses = []
    hit_but_not_1 = []
    n = 0
    hit5 = 0
    hit1 = 0
    for r in rows:
        exp = {
            d
            for d in (r.get("expected_chunk_sources") or r.get("expected_documents") or [])
            if d and d != "*"
        }
        if not exp:
            continue
        n += 1
        bm = bm25.search(r["query"], user_context=USER, top_n=cfg.bm25_top_n)
        dn = dense(r["query"])
        fused = rrf_fuse(bm, dn, k=args.k)
        reranked = reranker.rerank(r["query"], fused[: args.cand])[: cfg.final_top_k]

        final_rank = _rank_of(exp, reranked)
        if final_rank == 1:
            hit1 += 1
        if final_rank and final_rank <= cfg.final_top_k:
            hit5 += 1
            if final_rank != 1:
                hit_but_not_1.append(
                    {"id": r.get("query_id") or r.get("id"), "final_rank": final_rank}
                )
        else:
            misses.append(
                {
                    "id": r.get("query_id") or r.get("id") or r.get("query", "")[:40],
                    "query": r.get("query", "")[:80],
                    "expected": sorted(exp),
                    "rank_in_bm25": _rank_of(exp, bm),
                    "rank_in_dense": _rank_of(exp, dn),
                    "rank_in_fused": _rank_of(exp, fused),
                    "rank_in_reranked_top5": final_rank,
                }
            )

    report = {
        "config": {"k": args.k, "rerank_candidates": args.cand},
        "n": n,
        "hit_at_1": round(hit1 / n, 4) if n else 0,
        "recall_at_5": round(hit5 / n, 4) if n else 0,
        "n_misses": len(misses),
        "misses": misses,
        "n_hit_but_not_rank1": len(hit_but_not_1),
        "hit_but_not_rank1": hit_but_not_1,
    }
    print(f"n={n} recall@5={report['recall_at_5']} hit@1={report['hit_at_1']} misses={len(misses)}")
    print("\n--- MISSES (where does the expected doc actually sit?) ---")
    for m in misses:
        print(
            f"  {m['id']}: bm25={m['rank_in_bm25']} dense={m['rank_in_dense']} "
            f"fused={m['rank_in_fused']} | exp={m['expected']}"
        )
    print(f"\n--- HITS ranked 2-5 (the Hit@1 gap): {len(hit_but_not_1)} ---")
    for h in hit_but_not_1:
        print(f"  {h['id']}: final_rank={h['final_rank']}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
