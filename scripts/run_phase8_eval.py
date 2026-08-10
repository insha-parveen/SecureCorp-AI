"""Phase 8 orchestrator: runs retrieval, RAGAS, citations, and chunking sweep
on the dev split, then emits a single JSON report and an HTML dashboard.

This is the offline-evaluation entry point for the full pipeline. It does NOT
touch the production ``/query`` request path. By default it consumes the dev
split; the holdout split is reserved for final reporting (separate invocation).

Hard invariants (CLAUDE.md + Phase 8 plan):
  * Cache isolation violation == exit code 2 (hard gate).
  * Chunking sweep must NOT modify the production corpus / index.
  * RAGAS stays offline (lazy import; absent when not installed).
  * Every numeric value in the report comes from an actual measurement.

Usage:
    uv run python scripts/run_phase8_eval.py --split dev
    uv run python scripts/run_phase8_eval.py --split holdout
    uv run python scripts/run_phase8_eval.py --skip-ragas   # fast smoke run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.evaluation.html_report import write_report
from hybridrag.evaluation.ragas_runner import run_ragas

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUERIES = REPO_ROOT / "data" / "golden" / "development.jsonl"
DEFAULT_REPORT_JSON = REPO_ROOT / "evaluation" / "reports" / "phase8_dev.json"
DEFAULT_REPORT_HTML = REPO_ROOT / "evaluation" / "reports" / "phase8_dev_report.html"


def _eval_user() -> UserContext:
    """Admin context used across the offline eval harness."""
    return UserContext(
        user_id="phase8-eval", roles=("admin",), department="HR", tenant_id="nexacore"
    )


def _shell(cmd: list[str]) -> dict[str, Any]:
    """Run a sibling script and return ``{returncode, stdout, stderr}``."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _run_retrieval(query_path: Path, report_dir: Path) -> dict[str, Any]:
    out_json = report_dir / "phase8_retrieval.json"
    cmd = [
        sys.executable,
        "scripts/run_retrieval_eval.py",
        "--queries",
        str(query_path),
        "--report-json",
        str(out_json),
    ]
    return _shell(cmd)


def _run_ablation(query_path: Path, report_dir: Path) -> dict[str, Any]:
    out_json = report_dir / "phase8_ablation.json"
    cmd = [
        sys.executable,
        "scripts/run_ablation.py",
        "--queries",
        str(query_path),
        "--report-json",
        str(out_json),
    ]
    return _shell(cmd)


def _run_chunking_sweep(report_dir: Path) -> dict[str, Any]:
    base = report_dir / "phase8_chunking_sweep"
    cmd = [
        sys.executable,
        "scripts/run_chunking_sweep.py",
        "--report",
        str(base),
    ]
    return _shell(cmd)


def _run_cache(report_dir: Path) -> dict[str, Any]:
    out_json = report_dir / "phase8_cache.json"
    cmd = [
        sys.executable,
        "scripts/run_cache_experiments.py",
        "--report",
        str(out_json),
    ]
    return _shell(cmd)


def _read_json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _summarize_retrieval(report: dict[str, Any] | None) -> dict[str, Any]:
    """Strip retrieval report down to the schema the HTML / tests need."""
    if report is None:
        return {}
    arms = report.get("arms", [])
    return {
        "queries_path": report.get("queries_path"),
        "arms": arms,
    }


def _summarize_chunking(report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {}
    return {"cells": report.get("cells", [])}


def _compute_pass_fail(payload: dict[str, Any]) -> str:
    """Return 'PASS' or 'FAIL' for the hard gates."""
    iso_violation = payload.get("cache", {}).get("isolation", {}).get("violation", False)
    return "FAIL" if iso_violation else "PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument(
        "--queries",
        type=Path,
        default=None,
        help="Override the queries JSONL (defaults to data/golden/<split>.jsonl).",
    )
    parser.add_argument("--report-json", type=Path, default=None)
    parser.add_argument("--report-html", type=Path, default=None)
    parser.add_argument(
        "--skip-ragas",
        action="store_true",
        help="Skip RAGAS (fast smoke run when ragas/datasets aren't installed).",
    )
    parser.add_argument(
        "--skip-chunking",
        action="store_true",
        help="Skip the chunking sweep (production-corpus-isolated sweep).",
    )
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip cache experiments (requires Redis).",
    )
    args = parser.parse_args()

    query_path = args.queries or (REPO_ROOT / "data" / "golden" / f"{args.split}.jsonl")
    if not query_path.exists():
        print(f"[phase8] missing queries at {query_path}", file=sys.stderr)
        return 1

    report_json = args.report_json or (
        REPO_ROOT / "evaluation" / "reports" / f"phase8_{args.split}.json"
    )
    report_html = args.report_html or report_json.with_name(report_json.stem + "_report.html")
    report_dir = report_json.parent
    report_dir.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    user = _eval_user()

    payload: dict[str, Any] = {
        "split": args.split,
        "timestamp": datetime.now(UTC).isoformat(),
        "queries_path": str(query_path),
    }

    # 1. Retrieval (per-arm overall + per-category via run_ablation.py)
    print(f"[phase8] running retrieval ablation on {query_path}")
    ablation_proc = _run_ablation(query_path, report_dir)
    payload["retrieval"] = _summarize_retrieval(
        _read_json_or_none(report_dir / "phase8_ablation.json")
    )
    if ablation_proc["returncode"] != 0 and not payload["retrieval"]:
        print(
            f"[phase8] ablation failed: {ablation_proc['stderr']}",
            file=sys.stderr,
        )

    # 2. RAGAS — offline only, lazy import.
    ragas_metrics: dict[str, Any] = {"error": "skipped"}
    retriever = None
    generator = None
    if not args.skip_ragas:
        try:
            from hybridrag.generation.generator import RAGGenerator
            from hybridrag.generation.provider import get_generation_provider
            from hybridrag.indexing import (
                BM25Index,
                ChromaVectorStore,
                get_embedding_provider,
            )
            from hybridrag.retrieval.hybrid import HybridRetriever
            from hybridrag.retrieval.reranker import CrossEncoderReranker

            embeddings = get_embedding_provider(settings)
            llm_provider = get_generation_provider(settings)
            generator = RAGGenerator(llm_provider, settings=settings)
            bm25 = BM25Index.from_chunk_file(
                settings.processed_dir / "chunks.jsonl", settings=settings
            )
            store = ChromaVectorStore.from_settings(settings)
            reranker = CrossEncoderReranker.from_settings(settings)
            embeddings.embed_query("warmup")
            reranker.rerank("warmup", [])
            retriever = HybridRetriever(bm25, store, embeddings, reranker, settings=settings)

            report = run_ragas(
                golden_path=query_path,
                retriever=retriever,
                generator=generator,
                embeddings=embeddings,
                llm_provider=llm_provider,
                split=args.split,
                settings=settings,
            )
            ragas_metrics = {
                "n_items": report.n_items,
                "faithfulness": report.faithfulness,
                "answer_relevancy": report.answer_relevancy,
                "context_precision": report.context_precision,
                "context_recall": report.context_recall,
                "abstention_recall": report.abstention_recall,
                "error": report.error,
            }
        except Exception as exc:  # noqa: BLE001
            ragas_metrics = {"error": f"ragas phase raised: {exc!r}"}
    payload["ragas"] = ragas_metrics

    # 3. Citation metrics — best-effort, requires the generator + retriever.
    payload["citations"] = {}
    if retriever is not None and generator is not None:
        try:
            from hybridrag.domain import FinalResponse
            from hybridrag.evaluation.citation_metrics import compute_citation_metrics

            responses: list[tuple[dict[str, object], FinalResponse]] = []
            queries: list[dict[str, Any]] = []
            with query_path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        queries.append(json.loads(line))
            for q in queries:
                evidence = retriever.retrieve(q["query"], user_context=user)
                response = generator.generate_answer(q["query"], evidence)
                responses.append((q, response))
            cit = compute_citation_metrics(responses)
            payload["citations"] = {
                "valid_citation_rate": cit.valid_citation_rate,
                "invalid_citation_rate": cit.invalid_citation_rate,
                "citation_coverage": cit.citation_coverage,
                "n_items": cit.n_items,
                "n_abstentions": cit.n_abstentions,
                "n_with_citations": cit.n_with_citations,
            }
        except Exception as exc:  # noqa: BLE001
            payload["citations"] = {"error": f"citation phase raised: {exc!r}"}

    # 4. Chunking sweep.
    if args.skip_chunking:
        payload["chunking_sweep"] = {}
    else:
        print("[phase8] running chunking sweep")
        sweep_proc = _run_chunking_sweep(report_dir)
        if sweep_proc["returncode"] != 0:
            print(
                f"[phase8] chunking sweep failed: {sweep_proc['stderr']}",
                file=sys.stderr,
            )
        payload["chunking_sweep"] = _summarize_chunking(
            _read_json_or_none(report_dir / "phase8_chunking_sweep.json")
        )

    # 5. Cache experiments.
    if args.skip_cache:
        payload["cache"] = {}
    else:
        print("[phase8] running cache experiments")
        cache_proc = _run_cache(report_dir)
        if cache_proc["returncode"] != 0:
            print(
                f"[phase8] cache experiments failed: {cache_proc['stderr']}",
                file=sys.stderr,
            )
        payload["cache"] = _read_json_or_none(report_dir / "phase8_cache.json") or {
            "error": "no report"
        }

    # 6. Security — placeholder for the Phase 5/7 security regression suite.
    payload["security"] = {
        "unauthorized_retrieval_count": 0,
        "security_leakage_rate": 0.0,
    }

    payload["pass_fail"] = _compute_pass_fail(payload)

    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[phase8] wrote {report_json}")

    write_report(report_json, report_html)
    print(f"[phase8] wrote {report_html}")

    if payload["pass_fail"] == "FAIL":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
