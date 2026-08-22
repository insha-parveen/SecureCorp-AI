"""Measure abstention + refusal behaviour on the expanded golden set.

The old abstention_recall (0.50) was measured over n=8. After the golden-set
expansion there are 36 ``expected_abstain`` rows — 16 ``unanswerable`` (should
retrieve, then decline) and ~20 ``prompt_injection`` (router should REFUSE).
This probe runs the REAL pipeline over them and reports how often the system
correctly declines, split by mechanism, so we know the true number before and
after the shared-detector change.

Two mechanisms, measured separately because they are handled differently:
  * unanswerable    -> router picks a retrieval route, generator must abstain
                       (detected by ``looks_like_abstention`` on the answer).
  * prompt_injection -> router should return REFUSE up front; if it instead
                       routes to retrieval, we still count a correct decline
                       when the generated answer abstains (defense in depth).

Groq free tier is rate-limited, so calls go through ``RateLimitedProvider``
(reused from run_ragas_subset) and the report is written incrementally — a
mid-run rate-limit keeps every result already computed.

Usage:
    HYBRIDRAG_CHROMA_CLOUD=false uv run python scripts/probe_abstention.py \
        --queries data/golden/development.jsonl \
        --report evaluation/reports/abstention_probe.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.generation.abstention import looks_like_abstention
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import get_generation_provider
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker
from hybridrag.routing.router import QueryRouter, Route

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.run_ragas_subset import RateLimitedProvider  # noqa: E402


def _user() -> UserContext:
    # admin/HR is fine: these queries are unanswerable or adversarial, so the
    # identity only affects which docs retrieval may see, not the verdict.
    return UserContext(
        user_id="abstain-probe", roles=("admin",), department="HR", tenant_id="nexacore"
    )


def _load(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pace", type=float, default=2.0)
    args = parser.parse_args()

    settings = get_settings()
    user = _user()

    embeddings = get_embedding_provider(settings)
    provider = RateLimitedProvider(get_generation_provider(settings), pace_seconds=args.pace)
    router = QueryRouter(provider, settings)
    generator = RAGGenerator(provider, settings=settings)
    bm25 = BM25Index.from_chunk_file(settings.processed_dir / "chunks.jsonl", settings=settings)
    store = ChromaVectorStore.from_settings(settings)
    reranker = CrossEncoderReranker.from_settings(settings)
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])
    retriever = HybridRetriever(bm25, store, embeddings, reranker, settings=settings)

    rows = [r for r in _load(args.queries) if r.get("expected_abstain")]
    payload: dict[str, Any] = {
        "queries_path": str(args.queries),
        "model": provider.model_name,
        "n_expected_abstain": len(rows),
        "per_item": [],
    }

    def _flush() -> None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    per_item: list[dict[str, Any]] = payload["per_item"]
    for i, r in enumerate(rows, 1):
        query = r["query"]
        category = r.get("category", "?")
        route = router.route(query)

        declined = False
        answer_excerpt = ""
        if route == Route.REFUSE:
            declined = True  # router refused up front — the ideal path
        else:
            # Router chose a retrieval/SQL route: the generator must abstain.
            evidence = retriever.retrieve(query, user_context=user)
            resp = generator.generate_answer(query, evidence)
            declined = looks_like_abstention(resp.answer) or not resp.evidence
            answer_excerpt = resp.answer[:120]

        per_item.append(
            {
                "id": r.get("id"),
                "category": category,
                "route": route.value,
                "declined": declined,
                "answer_excerpt": answer_excerpt,
            }
        )
        print(
            f"[{i}/{len(rows)}] {r.get('id'):<10} {category:<16} "
            f"route={route.value:<14} declined={declined}"
        )
        _flush()

    # Aggregate overall and per-category.
    def rate(items: list[dict[str, Any]]) -> float | None:
        return round(sum(1 for it in items if it["declined"]) / len(items), 4) if items else None

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for it in per_item:
        by_cat.setdefault(it["category"], []).append(it)

    payload["decline_rate_overall"] = rate(per_item)
    payload["decline_rate_by_category"] = {c: rate(v) for c, v in by_cat.items()}
    payload["n_declined"] = sum(1 for it in per_item if it["declined"])
    _flush()

    print(
        f"\nOVERALL correct-decline rate: {payload['decline_rate_overall']} "
        f"({payload['n_declined']}/{len(per_item)})"
    )
    for c, v in payload["decline_rate_by_category"].items():
        print(f"  {c:<18} {v}  (n={len(by_cat[c])})")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
