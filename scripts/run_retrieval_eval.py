"""Ablation study for HybridRAG retrieval.
Compares Dense, BM25, RRF-fused, and Reranked results across a golden query set.
"""

import argparse
import json
from pathlib import Path

from hybridrag.evaluation.retrieval_eval import run_ablation_study


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queries",
        type=Path,
        default="evaluation/retrieval_eval/retrieval_queries.json",
        help="Path to the golden query set",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to write a JSON report of the per-arm overall metrics.",
    )
    args = parser.parse_args()

    print("Running Retrieval Ablation Study...")
    print(f"Dataset: {args.queries}")
    print("-" * 60)

    try:
        metrics = run_ablation_study(args.queries)

        print(f"{'Strategy':<20} | {'Recall@5':<10} | {'MRR':<10} | {'Hits'}")
        print("-" * 60)
        for m in metrics:
            print(
                f"{m.strategy:<20} | {m.recall_at_k:<10.2%} | {m.mrr:<10.3f} | {m.hits}/{m.total}"
            )

        if args.report_json is not None:
            payload = {
                "queries_path": str(args.queries),
                "arms": [
                    {
                        "strategy": m.strategy,
                        "recall_at_k": m.recall_at_k,
                        "mrr": m.mrr,
                        "ndcg_at_k": m.ndcg_at_k,
                        "precision_at_k": m.precision_at_k,
                        "hit_at_1": m.hit_at_1,
                        "hits": m.hits,
                        "total": m.total,
                    }
                    for m in metrics
                ],
            }
            args.report_json.parent.mkdir(parents=True, exist_ok=True)
            args.report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"\nWrote JSON report to {args.report_json}")

    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
