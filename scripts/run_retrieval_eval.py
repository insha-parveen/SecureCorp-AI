"""Ablation study for HybridRAG retrieval.
Compares Dense, BM25, RRF-fused, and Reranked results across a golden query set.
"""

import argparse
from pathlib import Path

from hybridrag.config import get_settings
from hybridrag.evaluation.retrieval_eval import run_ablation_study


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queries",
        type=Path,
        default="evaluation/retrieval_eval/retrieval_queries.json",
        help="Path to the golden query set"
    )
    args = parser.parse_args()

    print(f"Running Retrieval Ablation Study...")
    print(f"Dataset: {args.queries}")
    print("-" * 60)

    try:
        metrics = run_ablation_study(args.queries)

        print(f"{'Strategy':<20} | {'Recall@5':<10} | {'MRR':<10} | {'Hits'}")
        print("-" * 60)
        for m in metrics:
            print(f"{m.strategy:<20} | {m.recall_at_k:<10.2%} | {m.mrr:<10.3f} | {m.hits}/{m.total}")

    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
