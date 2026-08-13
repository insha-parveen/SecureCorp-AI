"""RAGAS runner — build the RAGAS Dataset and run the four core metrics.

Imports ``ragas`` lazily so the offline evaluation suite stays opt-in. If
ragas isn't installed, ``run_ragas`` records the error in its report and
returns gracefully — the orchestrator treats that as a non-fatal miss, not
a hard failure.

Metrics computed (per CLAUDE.md §13.2):
- faithfulness
- answer_relevancy
- context_precision
- context_recall

Plus an explicit ``abstention_recall`` computed against golden
``expected_abstain=true`` rows: it is the fraction of unanswerable items
where the assistant correctly abstained. RAGAS itself returns NaN on
abstentions (issue #772) so we don't rely on it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings
from hybridrag.domain import FinalResponse
from hybridrag.evaluation.ragas_adapter import ProjectRagasEmbeddings, ProjectRagasLLM
from hybridrag.evaluation.retrieval_eval import _load_queries
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import GenerationProvider
from hybridrag.indexing.embeddings import EmbeddingProvider
from hybridrag.retrieval.hybrid import HybridRetriever


@dataclass(frozen=True)
class RagasReport:
    """Result of one RAGAS run.

    All metric fields default to ``None`` and are populated only when RAGAS
    actually produced them. ``error`` is non-empty only on a hard failure
    (ragas not installed, dataset build error, etc.).
    """

    split: str
    n_items: int
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    abstention_recall: float | None = None
    error: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def _build_rows(
    queries: list[dict[str, Any]],
    retriever: HybridRetriever,
    generator: RAGGenerator,
    user_context_for: Callable[[dict[str, Any]], UserContext],
) -> tuple[list[dict[str, Any]], float | None]:
    """Build the rows consumed by ``datasets.Dataset``.

    Returns ``(rows, abstention_recall_or_none)``. ``rows`` is empty on a hard
    failure (the caller records the error itself) and ``abstention_recall_or_none``
    is the fraction of ``expected_abstain=true`` items where the assistant
    abstained correctly.
    """
    rows: list[dict[str, Any]] = []
    n_should_abstain = 0
    n_did_abstain = 0

    for q in queries:
        user = user_context_for(q)
        query_text = q["query"]
        expected_answer = q.get("expected_answer", "")
        expected_abstain = bool(q.get("expected_abstain", False))

        try:
            evidence = retriever.retrieve(query_text, user_context=user)
            response: FinalResponse = generator.generate_answer(query_text, evidence)
        except Exception as exc:  # noqa: BLE001 — keep RAGAS runner defensive
            raise RuntimeError(f"row build failed at id={q.get('id', '?')}: {exc!r}") from exc

        # Abstention accounting against the golden truth.
        if expected_abstain:
            n_should_abstain += 1
            answer_lower = response.answer.lower()
            if any(
                marker in answer_lower
                for marker in (
                    "do not know",
                    "insufficient information",
                    "outside my scope",
                    "i cannot answer",
                    "i am sorry",
                )
            ):
                n_did_abstain += 1

        contexts = [rc.chunk.text for rc in response.evidence]

        rows.append(
            {
                "question": query_text,
                "contexts": contexts,
                "answer": response.answer,
                "ground_truth": expected_answer,
            }
        )

    abstention_recall = (n_did_abstain / n_should_abstain) if n_should_abstain > 0 else None
    return rows, abstention_recall


def run_ragas(
    golden_path: Path,
    retriever: HybridRetriever,
    generator: RAGGenerator,
    embeddings: EmbeddingProvider,
    llm_provider: GenerationProvider,
    user_context_for: Callable[[dict[str, Any]], UserContext] | None = None,
    split: str = "dev",
    settings: Settings | None = None,
) -> RagasReport:
    """Run RAGAS over the golden set.

    ``user_context_for`` is a function that maps a golden row to its
    UserContext (so we can vary tenant/role per row). Defaults to the admin
    eval context, which mirrors ``RetrievalEvaluator``.
    """
    del settings  # unused — kept for future per-split settings overrides
    queries = _load_queries(golden_path)
    ctx_for = user_context_for or (
        lambda _q: UserContext(
            user_id="ragas-eval", roles=("admin",), department="HR", tenant_id="nexacore"
        )
    )

    try:
        rows, abstention_recall = _build_rows(queries, retriever, generator, ctx_for)
    except Exception as exc:  # noqa: BLE001
        return RagasReport(
            split=split,
            n_items=len(queries),
            error=f"row build failed: {exc!r}",
        )

    try:
        # ragas + datasets are optional eval-only deps; import lazily.
        import ragas  # type: ignore[import-not-found]
        from datasets import Dataset  # type: ignore[import-not-found]
        from ragas.metrics import (  # type: ignore[import-not-found]
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except Exception as exc:  # noqa: BLE001 — record, don't crash
        return RagasReport(
            split=split,
            n_items=len(queries),
            error=f"ragas/datasets not installed: {exc!r}",
            abstention_recall=abstention_recall,
        )

    dataset = Dataset.from_list(rows)
    ragas_llm = ProjectRagasLLM(llm_provider)
    ragas_emb = ProjectRagasEmbeddings(embeddings)

    try:
        result = ragas.evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=ragas_llm,
            embeddings=ragas_emb,
        )
    except Exception as exc:  # noqa: BLE001
        return RagasReport(
            split=split,
            n_items=len(queries),
            error=f"ragas.evaluate raised: {exc!r}",
            abstention_recall=abstention_recall,
        )

    # ragas returns an EvaluationResult; coerce to a flat dict if possible.
    scores: dict[str, float] = {}
    try:
        df = result.to_pandas() if hasattr(result, "to_pandas") else None
        if df is not None and not df.empty:
            for col in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
                if col in df.columns:
                    scores[col] = float(df[col].mean())
    except Exception:  # noqa: BLE001
        pass

    return RagasReport(
        split=split,
        n_items=len(queries),
        faithfulness=scores.get("faithfulness"),
        answer_relevancy=scores.get("answer_relevancy"),
        context_precision=scores.get("context_precision"),
        context_recall=scores.get("context_recall"),
        abstention_recall=abstention_recall,
    )


def write_report(report: RagasReport, path: Path) -> None:
    """Serialize a RagasReport to JSON. Empty/None values become ``null``."""
    payload = {
        "split": report.split,
        "n_items": report.n_items,
        "faithfulness": report.faithfulness,
        "answer_relevancy": report.answer_relevancy,
        "context_precision": report.context_precision,
        "context_recall": report.context_recall,
        "abstention_recall": report.abstention_recall,
        "error": report.error,
        "extra": report.extra,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
