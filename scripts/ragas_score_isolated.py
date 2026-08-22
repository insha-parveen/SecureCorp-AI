"""STEP 2 of the isolated RAGAS pipeline — runs in a SEPARATE venv (.venv-ragas).

Scores the rows dumped by ``scripts/dump_ragas_rows.py`` with the four RAGAS
core metrics. This file deliberately imports NOTHING from ``hybridrag`` and no
torch-heavy retrieval stack — it only needs ragas + datasets + a small
embedding model + an HTTP LLM. That is what makes it safe to install a
ragas/langchain combination here that would otherwise clobber the main venv.

Design choices that keep the isolated env small and conflict-free:
  * ragas 0.1.x native API: ``evaluate(dataset, metrics=[...], llm=, embeddings=)``
    with the column names {question, contexts, answer, ground_truth} — exactly
    what STEP 1 writes.
  * LLM judge = Groq via its OpenAI-COMPATIBLE endpoint through
    ``langchain_openai.ChatOpenAI`` (no ``langchain-groq`` package needed, so no
    fight over langchain-core versions). Same model as production
    (llama-3.3-70b-versatile), so the judge is representative.
  * Embeddings = local sentence-transformers MiniLM (answer_relevancy only needs
    a similarity space; it need not match the retrieval embedding).
  * ``max_workers=1`` + generous retry/wait so Groq's 12k TPM free tier does not
    trip the run.

The Groq key is read from ``$GROQ_API_KEY`` in the environment (the caller
passes it through from HYBRIDRAG_GROQ_API_KEY). It is never printed.

Usage (isolated venv):
    uv venv .venv-ragas --python 3.11
    uv pip install --python .venv-ragas "ragas==0.1.21" "langchain-openai" \
        "sentence-transformers" "datasets"
    GROQ_API_KEY=... .venv-ragas/Scripts/python scripts/ragas_score_isolated.py \
        --rows evaluation/reports/ragas_rows_dev.jsonl \
        --report evaluation/reports/phase8_ragas_isolated.json \
        --model llama-3.3-70b-versatile
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any


def _load_rows(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _clean(value: Any) -> float | None:
    """Coerce a metric cell to float, mapping NaN/None to None for JSON."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument(
        "--base-url",
        default="https://api.groq.com/openai/v1",
        help="OpenAI-compatible endpoint. Groq by default; pass "
        "http://localhost:11434/v1 to use a local Ollama model as the judge.",
    )
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args()

    # A local endpoint (Ollama) needs no real key — langchain_openai still
    # requires a non-empty string, so pass a harmless placeholder. A remote
    # endpoint (Groq) reads the real key from $GROQ_API_KEY and never prints it.
    is_local = "localhost" in args.base_url or "127.0.0.1" in args.base_url
    if is_local:
        api_key = os.environ.get("GROQ_API_KEY", "").strip() or "ollama-local-no-key"
    else:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            print("[ragas_isolated] ERROR: GROQ_API_KEY not set in environment")
            return 2

    rows = _load_rows(args.rows)
    # RAGAS context_recall / context_precision need a non-empty ground_truth.
    # Rows without an expected answer would return NaN and drag the mean down,
    # so we score only rows that have one, and report how many were used.
    scorable = [r for r in rows if str(r.get("ground_truth", "")).strip()]
    payload: dict[str, Any] = {
        "rows_path": str(args.rows),
        "n_rows_total": len(rows),
        "n_rows_scored": len(scorable),
        "model": args.model,
        "judge_endpoint": args.base_url,
        "embedding_model": args.embedding_model,
    }

    def _flush() -> None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not scorable:
        payload["error"] = "no rows with a non-empty ground_truth to score"
        _flush()
        print(f"[ragas_isolated] {payload['error']}")
        return 1

    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from ragas.run_config import RunConfig

        # Local MiniLM via sentence-transformers, wrapped for ragas/langchain.
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except Exception:  # noqa: BLE001 — older stacks ship it under community
            from langchain_community.embeddings import HuggingFaceEmbeddings
    except Exception as exc:  # noqa: BLE001
        payload["error"] = f"import failed in isolated env: {type(exc).__name__}: {exc}"
        _flush()
        print(f"[ragas_isolated] {payload['error']}")
        return 1

    # Judge LLM via an OpenAI-compatible endpoint (Groq or local Ollama).
    # temperature=0 for determinism. Local models can be slow per call, so the
    # timeout is generous; there is no server-side rate limit to back off from.
    llm = ChatOpenAI(
        model=args.model,
        api_key=api_key,
        base_url=args.base_url,
        temperature=0.0,
        max_retries=6,
        timeout=600 if is_local else 120,
    )
    embeddings = HuggingFaceEmbeddings(model_name=args.embedding_model)

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    metric_cols = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    run_config = RunConfig(max_workers=args.max_workers, max_retries=10, max_wait=90)

    # Resume: reuse any per-item scores already written to the report. This is
    # what makes the run kill-resilient — a killed process costs at most the one
    # item in flight, and re-launching finishes the rest.
    done_by_id: dict[str, dict[str, Any]] = {}
    if args.report.exists():
        try:
            prev = json.loads(args.report.read_text(encoding="utf-8"))
            for it in prev.get("per_item", []):
                if it.get("id") is not None:
                    done_by_id[str(it["id"])] = it
        except Exception:  # noqa: BLE001 — a corrupt/partial file just means "start over"
            done_by_id = {}

    def _aggregate(items: list[dict[str, Any]]) -> dict[str, float | None]:
        agg: dict[str, float | None] = {}
        for col in metric_cols:
            present = [it[col] for it in items if it.get(col) is not None]
            agg[col] = round(sum(present) / len(present), 4) if present else None
        return agg

    per_item: list[dict[str, Any]] = []
    payload["error"] = ""

    print(
        f"[ragas_isolated] scoring {len(scorable)} rows with {args.model} "
        f"({len(done_by_id)} already done) ..."
    )
    for idx, row in enumerate(scorable, 1):
        rid = str(row.get("id", idx))
        if rid in done_by_id:
            per_item.append(done_by_id[rid])
            print(f"[ragas_isolated]   {idx}/{len(scorable)} id={rid} (cached)")
        else:
            entry: dict[str, Any] = {
                "id": rid,
                "question": str(row.get("question", ""))[:80],
            }
            try:
                one = Dataset.from_list(
                    [
                        {
                            "question": row["question"],
                            "contexts": list(row.get("contexts", [])),
                            "answer": row.get("answer", ""),
                            "ground_truth": row.get("ground_truth", ""),
                        }
                    ]
                )
                result = evaluate(
                    one, metrics=metrics, llm=llm, embeddings=embeddings, run_config=run_config
                )
                df = result.to_pandas()
                r0 = df.iloc[0]
                for col in metric_cols:
                    entry[col] = _clean(r0.get(col))
            except Exception as exc:  # noqa: BLE001 — one bad item must not sink the run
                for col in metric_cols:
                    entry[col] = None
                entry["item_error"] = f"{type(exc).__name__}: {exc}"
                print(f"[ragas_isolated]   {idx}/{len(scorable)} id={rid} FAILED: {exc}")
            else:
                print(
                    f"[ragas_isolated]   {idx}/{len(scorable)} id={rid} "
                    f"faith={entry['faithfulness']} ar={entry['answer_relevancy']} "
                    f"cp={entry['context_precision']} cr={entry['context_recall']}"
                )
            per_item.append(entry)

        # Write after every item so partial progress always survives a kill.
        payload["ragas"] = _aggregate(per_item)
        payload["per_item"] = per_item
        payload["n_scored_so_far"] = len(per_item)
        _flush()

    print(f"[ragas_isolated] ragas: {json.dumps(payload['ragas'])}")
    print(f"[ragas_isolated] wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
