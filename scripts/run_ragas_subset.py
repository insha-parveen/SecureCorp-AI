"""One-off: RAGAS + citation metrics over a stratified subset of the dev set.

Reuses the library's ``run_ragas`` and ``compute_citation_metrics`` (the same
code paths the Phase 8 orchestrator uses). Two accommodations for a Groq
free-tier account (12k tokens/minute):

* A ``RateLimitedProvider`` wraps the real provider and retries on HTTP 429,
  honoring Groq's suggested retry delay (exponential backoff otherwise). It
  also paces calls with a small inter-request sleep. It is a thin wrapper — it
  does NOT change the model, prompts, or output, so the metrics still reflect
  the production ``llama-3.3-70b-versatile`` path.
* Citations run over the full subset (1 generation/item); RAGAS runs over a
  capped subset (many judge calls/item). Partial results are always written,
  so a mid-run rate limit never discards what already succeeded.

Usage:
    HYBRIDRAG_CHROMA_CLOUD=false uv run python scripts/run_ragas_subset.py \
        --queries data/golden/ragas_subset_dev.jsonl \
        --report evaluation/reports/phase8_ragas_citations_subset.json \
        --ragas-limit 8
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import requests

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.domain import FinalResponse
from hybridrag.evaluation.citation_metrics import compute_citation_metrics
from hybridrag.evaluation.ragas_runner import run_ragas
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import (
    GenerationProvider,
    GenerationResponse,
    get_generation_provider,
)
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker

_RETRY_RE = re.compile(r"try again in ([0-9.]+)s")


class RateLimitedProvider:
    """Wrap a GenerationProvider with 429 retry/backoff + inter-call pacing.

    Satisfies the GenerationProvider protocol so it is a drop-in for both
    RAGGenerator and the RAGAS adapter. The wrapping is behavior-preserving
    (same model, prompts, output) — it only adds waiting.
    """

    def __init__(
        self,
        inner: GenerationProvider,
        *,
        max_retries: int = 8,
        pace_seconds: float = 2.0,
    ) -> None:
        self._inner = inner
        self._max_retries = max_retries
        self._pace_seconds = pace_seconds

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    def _sleep_for(self, exc: requests.HTTPError, attempt: int) -> None:
        delay = min(2.0 * (2**attempt), 30.0)  # exp backoff, capped
        body = ""
        if exc.response is not None:
            body = exc.response.text or ""
        m = _RETRY_RE.search(body)
        if m:
            delay = float(m.group(1)) + 0.5  # honor Groq's hint + margin
        time.sleep(delay)

    def generate(
        self, prompt: str, system_prompt: str | None = None, json_mode: bool = True
    ) -> GenerationResponse:
        last: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._inner.generate(
                    prompt, system_prompt=system_prompt, json_mode=json_mode
                )
                time.sleep(self._pace_seconds)  # proactive pacing under TPM
                return resp
            except requests.HTTPError as exc:
                last = exc
                status = exc.response.status_code if exc.response is not None else None
                # 429 = rate limit (honor the retry hint); 5xx = transient Groq
                # server error (plain backoff). Both are worth retrying rather
                # than losing a whole eval run; 4xx other than 429 are fatal.
                if status == 429 or (status is not None and 500 <= status < 600):
                    self._sleep_for(exc, attempt)
                    continue
                raise
        raise RuntimeError(f"exhausted {self._max_retries} retries") from last

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        return self._inner.stream(prompt, system_prompt=system_prompt)


def _user() -> UserContext:
    return UserContext(
        user_id="ragas-subset", roles=("admin",), department="HR", tenant_id="nexacore"
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
    parser.add_argument(
        "--ragas-limit",
        type=int,
        default=8,
        help="Max items for the (expensive) RAGAS phase. Citations use the full set.",
    )
    parser.add_argument("--pace", type=float, default=2.0, help="Inter-call pacing seconds.")
    args = parser.parse_args()

    settings = get_settings()
    user = _user()

    embeddings = get_embedding_provider(settings)
    raw_provider = get_generation_provider(settings)
    provider = RateLimitedProvider(raw_provider, pace_seconds=args.pace)
    generator = RAGGenerator(provider, settings=settings)
    bm25 = BM25Index.from_chunk_file(settings.processed_dir / "chunks.jsonl", settings=settings)
    store = ChromaVectorStore.from_settings(settings)
    reranker = CrossEncoderReranker.from_settings(settings)
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])
    retriever = HybridRetriever(bm25, store, embeddings, reranker, settings=settings)

    queries = _load(args.queries)
    payload: dict[str, Any] = {
        "queries_path": str(args.queries),
        "n_items_total": len(queries),
        "model": provider.model_name,
        "ragas": {"error": "not run"},
        "citations": {"error": "not run"},
    }

    def _flush() -> None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # --- Citations first (cheap: 1 generation/item), full subset ---
    print(f"[ragas_subset] computing citation metrics over {len(queries)} items")
    try:
        responses: list[tuple[dict[str, object], FinalResponse]] = []
        for i, q in enumerate(queries, 1):
            evidence = retriever.retrieve(q["query"], user_context=user)
            response = generator.generate_answer(q["query"], evidence)
            responses.append((q, response))
            if i % 5 == 0:
                print(f"[ragas_subset]   {i}/{len(queries)} generated")
        cit = compute_citation_metrics(responses)
        payload["citations"] = {
            "n_items": cit.n_items,
            "valid_citation_rate": cit.valid_citation_rate,
            "invalid_citation_rate": cit.invalid_citation_rate,
            "citation_coverage": cit.citation_coverage,
            "n_abstentions": cit.n_abstentions,
            "n_with_citations": cit.n_with_citations,
        }
        print(f"[ragas_subset] citations: {json.dumps(payload['citations'])}")
    except Exception as exc:  # noqa: BLE001
        payload["citations"] = {"error": f"{type(exc).__name__}: {exc}"}
        print(f"[ragas_subset] citations FAILED: {exc}")
    _flush()

    # --- RAGAS (expensive: many judge calls/item), capped subset ---
    ragas_queries = queries[: args.ragas_limit]
    ragas_path = args.queries.with_name(args.queries.stem + f"_ragas{len(ragas_queries)}.jsonl")
    with ragas_path.open("w", encoding="utf-8") as fh:
        for q in ragas_queries:
            fh.write(json.dumps(q) + "\n")
    print(f"[ragas_subset] running RAGAS over {len(ragas_queries)} items ({ragas_path.name})")
    try:
        report = run_ragas(
            golden_path=ragas_path,
            retriever=retriever,
            generator=generator,
            embeddings=embeddings,
            llm_provider=provider,
            split="dev-subset",
            settings=settings,
        )
        payload["ragas"] = {
            "n_items": report.n_items,
            "faithfulness": report.faithfulness,
            "answer_relevancy": report.answer_relevancy,
            "context_precision": report.context_precision,
            "context_recall": report.context_recall,
            "abstention_recall": report.abstention_recall,
            "error": report.error,
        }
        print(f"[ragas_subset] ragas: {json.dumps(payload['ragas'])}")
    except Exception as exc:  # noqa: BLE001
        payload["ragas"] = {"error": f"{type(exc).__name__}: {exc}"}
        print(f"[ragas_subset] ragas FAILED: {exc}")
    _flush()

    print(f"[ragas_subset] wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
