"""CLI: run RAGAS over a golden split (dev or holdout).

This is the offline-evaluation entry point for RAGAS. It does NOT touch the
``/query`` request path. By default it reads ``data/golden/development.jsonl``
and writes ``evaluation/reports/ragas_<split>.json``.

Usage:
    uv run python scripts/run_ragas.py --split dev
    uv run python scripts/run_ragas.py --split holdout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hybridrag.config import get_settings
from hybridrag.evaluation.ragas_runner import run_ragas, write_report
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import get_generation_provider
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.indexing.embeddings import EmbeddingProvider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDEN_DIR = REPO_ROOT / "data" / "golden"
DEFAULT_REPORT_DIR = REPO_ROOT / "evaluation" / "reports"


def _build_hybrid_retriever(settings, embeddings: EmbeddingProvider) -> HybridRetriever:
    """Construct a HybridRetriever with all four retrieval components warm-loaded."""
    bm25 = BM25Index.from_chunk_file(settings.processed_dir / "chunks.jsonl", settings=settings)
    store = ChromaVectorStore.from_settings(settings)
    reranker = CrossEncoderReranker.from_settings(settings)
    embeddings.embed_query("warmup")  # fail-fast on missing model
    reranker.rerank("warmup", [])
    return HybridRetriever(bm25, store, embeddings, reranker, settings=settings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument(
        "--golden-dir",
        type=Path,
        default=DEFAULT_GOLDEN_DIR,
        help="Directory containing development.jsonl and holdout.jsonl.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="Output directory for the JSON report.",
    )
    args = parser.parse_args()

    golden_path = (
        args.golden_dir / "holdout.jsonl"
        if args.split == "holdout"
        else args.golden_dir / "development.jsonl"
    )
    if not golden_path.exists():
        print(f"[run_ragas] missing {golden_path}", file=sys.stderr)
        return 1

    settings = get_settings()
    embeddings = get_embedding_provider(settings)
    llm_provider = get_generation_provider(settings)
    generator = RAGGenerator(llm_provider, settings=settings)
    retriever = _build_hybrid_retriever(settings, embeddings)

    print(f"[run_ragas] split={args.split}  queries={golden_path}")
    report = run_ragas(
        golden_path=golden_path,
        retriever=retriever,
        generator=generator,
        embeddings=embeddings,
        llm_provider=llm_provider,
        split=args.split,
        settings=settings,
    )

    report_path = args.report_dir / f"ragas_{args.split}.json"
    write_report(report, report_path)
    print(f"[run_ragas] Wrote {report_path}")
    if report.error:
        print(f"[run_ragas] ERROR: {report.error}", file=sys.stderr)
        return 2
    print(
        f"[run_ragas] faithfulness={report.faithfulness} "
        f"answer_relevancy={report.answer_relevancy} "
        f"context_precision={report.context_precision} "
        f"context_recall={report.context_recall} "
        f"abstention_recall={report.abstention_recall}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
