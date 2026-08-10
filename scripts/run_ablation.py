"""CLI: run the 4-arm retrieval ablation on a golden split (dev or holdout).

This is the Phase 8 entry point for the retrieval ablation. Unlike
``run_retrieval_eval.py`` (which only emits the per-arm *overall* metrics), this
script emits the full ``DetailedRetrievalResult`` shape — per-arm overall metrics
plus a per-category breakdown — and writes BOTH a JSON report and a CSV table.

CSV schema (one row per arm × category):
    arm, category, recall_at_5, mrr, ndcg_at_5, precision_at_5, hits, total

JSON schema:
    {
      "queries_path": "...",
      "arms": [
        {
          "strategy": "Hybrid-Rerank",
          "overall": {...},
          "by_category": {"direct_factual": {...}, ...}
        },
        ...
      ]
    }

Default queries path: data/golden/development.jsonl

Usage:
    uv run python scripts/run_ablation.py
    uv run python scripts/run_ablation.py --queries data/golden/holdout.jsonl
    uv run python scripts/run_ablation.py --report-json evaluation/reports/ablation_dev.json \\
                                            --report-csv  evaluation/reports/ablation_dev.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from hybridrag.config import get_settings
from hybridrag.evaluation.retrieval_eval import run_ablation_study_detailed

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUERIES = REPO_ROOT / "data" / "golden" / "development.jsonl"
DEFAULT_REPORT_JSON = REPO_ROOT / "evaluation" / "reports" / "ablation_dev.json"
DEFAULT_REPORT_CSV = REPO_ROOT / "evaluation" / "reports" / "ablation_dev.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERIES,
        help="Path to the golden JSONL (or legacy JSON list) of queries.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=DEFAULT_REPORT_JSON,
        help="Output path for the JSON report.",
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        default=DEFAULT_REPORT_CSV,
        help="Output path for the CSV report (one row per arm × category).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="K for Recall@K / nDCG@K / Precision@K (default 5).",
    )
    args = parser.parse_args()

    if not args.queries.exists():
        print(f"[run_ablation] missing {args.queries}", file=sys.stderr)
        return 1

    print(f"[run_ablation] queries={args.queries}")
    settings = get_settings()

    try:
        results = run_ablation_study_detailed(args.queries, settings=settings)
    except Exception as exc:  # noqa: BLE001
        print(f"[run_ablation] evaluation failed: {exc!r}", file=sys.stderr)
        return 2

    # Console summary — overall metrics per arm
    header = (
        f"{'Strategy':<16} | {'Recall@5':>9} | {'MRR':>7} | {'nDCG@5':>8} | {'P@5':>6} | {'Hits'}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        m = r.overall
        print(
            f"{m.strategy:<16} | {m.recall_at_k:>9.2%} | {m.mrr:>7.3f} "
            f"| {m.ndcg_at_k:>8.3f} | {m.precision_at_k:>6.2%} | {m.hits}/{m.total}"
        )

    # JSON report
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "queries_path": str(args.queries),
        "arms": [
            {
                "strategy": r.strategy,
                "overall": {
                    "recall_at_k": r.overall.recall_at_k,
                    "mrr": r.overall.mrr,
                    "ndcg_at_k": r.overall.ndcg_at_k,
                    "precision_at_k": r.overall.precision_at_k,
                    "hit_at_1": r.overall.hit_at_1,
                    "hits": r.overall.hits,
                    "total": r.overall.total,
                },
                "by_category": {
                    cat: {
                        "recall_at_k": cat_m.recall_at_k,
                        "mrr": cat_m.mrr,
                        "ndcg_at_k": cat_m.ndcg_at_k,
                        "precision_at_k": cat_m.precision_at_k,
                        "hits": cat_m.hits,
                        "total": cat_m.total,
                    }
                    for cat, cat_m in r.by_category.items()
                },
            }
            for r in results
        ],
    }
    args.report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n[run_ablation] Wrote {args.report_json}")

    # CSV report — one row per (arm × category), plus a final "OVERALL" row per arm
    args.report_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.report_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "arm",
                "category",
                "recall_at_5",
                "mrr",
                "ndcg_at_5",
                "precision_at_5",
                "hits",
                "total",
            ]
        )
        for r in results:
            for cat, cat_m in sorted(r.by_category.items()):
                writer.writerow(
                    [
                        r.strategy,
                        cat,
                        f"{cat_m.recall_at_k:.4f}",
                        f"{cat_m.mrr:.4f}",
                        f"{cat_m.ndcg_at_k:.4f}",
                        f"{cat_m.precision_at_k:.4f}",
                        cat_m.hits,
                        cat_m.total,
                    ]
                )
            # OVERALL row for this arm
            writer.writerow(
                [
                    r.strategy,
                    "OVERALL",
                    f"{r.overall.recall_at_k:.4f}",
                    f"{r.overall.mrr:.4f}",
                    f"{r.overall.ndcg_at_k:.4f}",
                    f"{r.overall.precision_at_k:.4f}",
                    r.overall.hits,
                    r.overall.total,
                ]
            )
    print(f"[run_ablation] Wrote {args.report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
