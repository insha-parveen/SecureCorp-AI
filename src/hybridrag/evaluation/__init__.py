"""Phase 8 evaluation package.

Re-exports the public types for tests and downstream consumers.
"""

from hybridrag.evaluation.retrieval_eval import (
    DetailedRetrievalResult,
    PerCategoryMetrics,
    RetrievalEvaluator,
    RetrievalMetric,
    run_ablation_study,
    run_ablation_study_detailed,
)

__all__ = [
    "DetailedRetrievalResult",
    "PerCategoryMetrics",
    "RetrievalEvaluator",
    "RetrievalMetric",
    "run_ablation_study",
    "run_ablation_study_detailed",
]
