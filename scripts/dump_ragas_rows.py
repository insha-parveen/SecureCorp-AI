"""STEP 1 of the isolated RAGAS pipeline — runs in the MAIN venv.

Produces the {question, contexts, answer, ground_truth} rows that RAGAS scores,
reusing the exact production retrieval + generation path (HybridRetriever ->
RAGGenerator over the Groq provider, wrapped in the rate-limiter). It writes a
plain JSONL so STEP 2 (``scripts/ragas_score_isolated.py``) can score it in a
SEPARATE virtualenv whose ragas/langchain versions never touch this one.

Why two steps / two venvs: installed ``ragas`` can't even ``import`` here — it
was co-resolved with langchain 1.x, and ragas hard-imports a
``langchain_community.chat_models.vertexai`` module that langchain-community
removed. Downgrading langchain in THIS venv would clobber the retrieval/api
stack (torch, sentence-transformers, chromadb). So we keep generation here and
move only the scoring into an isolated env.

Usage (main venv):
    HYBRIDRAG_CHROMA_CLOUD=false uv run python scripts/dump_ragas_rows.py \
        --queries data/golden/ragas_subset_dev.jsonl \
        --out evaluation/reports/ragas_rows_dev.jsonl \
        --limit 8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.generation.generator import RAGGenerator
from hybridrag.generation.provider import get_generation_provider
from hybridrag.indexing import BM25Index, ChromaVectorStore, get_embedding_provider
from hybridrag.retrieval.hybrid import HybridRetriever
from hybridrag.retrieval.reranker import CrossEncoderReranker

# Make the repo root importable so ``scripts`` resolves as a namespace package
# regardless of cwd (``uv run python scripts/x.py`` puts scripts/ on sys.path,
# not the repo root). We reuse the tested Groq 429 rate-limiter rather than
# re-implementing it.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.run_ragas_subset import RateLimitedProvider  # noqa: E402


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
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=8, help="Max items to generate rows for.")
    parser.add_argument("--pace", type=float, default=2.0, help="Inter-call pacing seconds.")
    args = parser.parse_args()

    settings = get_settings()
    user = _user()

    embeddings = get_embedding_provider(settings)
    provider = RateLimitedProvider(get_generation_provider(settings), pace_seconds=args.pace)
    generator = RAGGenerator(provider, settings=settings)
    bm25 = BM25Index.from_chunk_file(settings.processed_dir / "chunks.jsonl", settings=settings)
    store = ChromaVectorStore.from_settings(settings)
    reranker = CrossEncoderReranker.from_settings(settings)
    embeddings.embed_query("warmup")
    reranker.rerank("warmup", [])
    retriever = HybridRetriever(bm25, store, embeddings, reranker, settings=settings)

    queries = _load(args.queries)[: args.limit]
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for i, q in enumerate(queries, 1):
            evidence = retriever.retrieve(q["query"], user_context=user)
            response = generator.generate_answer(q["query"], evidence)
            row = {
                "id": q.get("id", str(i)),
                "question": q["query"],
                "contexts": [rc.chunk.text for rc in response.evidence],
                "answer": response.answer,
                "ground_truth": q.get("expected_answer", ""),
                "expected_abstain": bool(q.get("expected_abstain", False)),
            }
            fh.write(json.dumps(row) + "\n")
            fh.flush()  # partial-write safe: a mid-run rate limit keeps prior rows
            written += 1
            n_ctx = len(row["contexts"])
            print(f"[dump_ragas_rows]   {i}/{len(queries)} generated (contexts={n_ctx})")

    print(f"[dump_ragas_rows] wrote {written} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
