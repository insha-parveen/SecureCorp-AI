"""Quantify the highest-leverage retrieval fix: the dense authorization pre-filter.

Dense-Only collapses under auth (30% on 80q) because
``AuthorizationEngine.build_dense_filter`` pushes only a NARROW ``where`` clause
to Chroma (public OR owner OR dept-internal) and OMITS role-based grants — so
authorized-but-role-gated docs never enter the candidate pool. BM25 does not
collapse because it post-filters ONLY (no narrowing pre-filter).

This probe measures Dense-Only and Hybrid-RRF (no reranker, so it stays fast)
on the 80q set under three dense regimes, holding the ``is_authorized``
post-filter (the real security boundary) constant in all three:

  R1 current   : where=build_dense_filter, top_k=50,  + post-filter  (production today)
  R2 no-where  : where=None,                top_k=50,  + post-filter  (like BM25)
  R3 no-where+ : where=None,                top_k=200, + post-filter  (over-fetch)

If R2/R3 >> R1, the narrow pre-filter is the bug and dropping it (relying on the
post-filter, which BM25 already does) recovers recall with zero security change.
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

USER = UserContext(user_id="eval", roles=("admin",), department="HR", tenant_id="nexacore")


def _score(rows, retrieve, k=5) -> tuple[float, float, int]:
    hits = h1 = n = 0
    for r in rows:
        exp = {
            d
            for d in set(r.get("expected_chunk_sources", r.get("expected_documents", [])))
            if d and d != "*"
        }
        if not exp:
            continue
        n += 1
        first = 0
        for rank, rc in enumerate(retrieve(r["query"]), start=1):
            if rc.chunk.document_id in exp:
                first = rank
                break
        if first and first <= k:
            hits += 1
        if first == 1:
            h1 += 1
    return round(hits / n, 4), round(h1 / n, 4), n


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
    emb.embed_query("warmup")

    def dense(q: str, *, use_where: bool, top_k: int) -> list[RankedChunk]:
        where = AuthorizationEngine.build_dense_filter(USER) if use_where else None
        out: list[RankedChunk] = []
        for r, m in enumerate(store.query(emb.embed_query(q), top_k=top_k, where=where), start=1):
            c = decode_chunk(m.text, m.metadata)
            if AuthorizationEngine.is_authorized(USER, c):  # security boundary, unchanged
                out.append(RankedChunk(chunk=c, score=float(m.distance), rank=r, retriever="dense"))
        return out

    regimes = {
        "R1_current_where_top50": dict(use_where=True, top_k=50),
        "R2_nowhere_top50": dict(use_where=False, top_k=50),
        "R3_nowhere_top200": dict(use_where=False, top_k=200),
    }

    out: dict = {"queries": str(args.queries), "regimes": {}}
    for name, kw in regimes.items():
        d_r5, d_h1, n = _score(rows, lambda q, kw=kw: dense(q, **kw)[: cfg.final_top_k])
        f_r5, f_h1, _ = _score(
            rows,
            lambda q, kw=kw: rrf_fuse(
                bm25.search(q, user_context=USER, top_n=cfg.bm25_top_n), dense(q, **kw)
            )[: cfg.final_top_k],
        )
        out["regimes"][name] = {
            "dense_only": {"recall_at_5": d_r5, "hit_at_1": d_h1},
            "hybrid_rrf_norerank": {"recall_at_5": f_r5, "hit_at_1": f_h1},
            "n": n,
        }
        print(f"{name:26s} Dense R@5={d_r5:<7} H@1={d_h1:<7} | HybridRRF R@5={f_r5:<7} H@1={f_h1}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
