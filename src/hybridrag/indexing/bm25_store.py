"""BM25 sparse/keyword retrieval over the same chunk corpus as the dense index.
CLAUDE.md §7: This retriever is the essential arm for exact identifiers, policy codes,
acronyms, and product names where dense retrieval often fails.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from hybridrag.authorization.engine import AuthorizationEngine
from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings
from hybridrag.domain import Chunk, RankedChunk
from hybridrag.ingestion.chunk_store import load_chunks

RETRIEVER_NAME = "bm25"

# Conservative stopword list to avoid eating corpus-meaningful short words like "it" (IT dept)
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "his",
        "if",
        "in",
        "into",
        "is",
        "its",
        "of",
        "on",
        "or",
        "our",
        "ours",
        "she",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
    ]
)

_TERM_RE = re.compile(r"[a-z0-9]+(?:[-_./][a-z0-9]+)*")
_ID_SEPARATORS = re.compile(r"[-_./]")


@dataclass
class BM25Params:
    """Parameters for BM25 retrieval. Defaults match industry standard (Okapi)."""

    k1: float = 1.5
    b: float = 0.75


def analyze(text: str, remove_stopwords: bool = True, expand_identifiers: bool = True) -> list[str]:
    """Turn text into BM25 terms with noise filtering.

    Rules:
    1. Drop single characters (markdown residue).
    2. Drop stopwords if enabled.
    3. Keep compound identifiers whole.
    4. Emit parts of compound identifiers if enabled.
    """
    terms: list[str] = []
    for match in _TERM_RE.findall(text.lower()):
        token = match
        # Drop single characters (markdown noise) and stopwords
        if len(token) < 2 or (remove_stopwords and token in STOPWORDS):
            continue

        terms.append(token)
        if expand_identifiers:
            parts = [part for part in _ID_SEPARATORS.split(token) if len(part) >= 2]
            if len(parts) > 1:
                terms.extend(parts)
    return terms


class BM25Index:
    """In-memory BM25 index over a chunk corpus, returning RankedChunk."""

    def __init__(
        self,
        chunks: Sequence[Chunk],
        *,
        k1: float | None = None,
        b: float | None = None,
        settings: Settings | None = None,
    ) -> None:
        config = settings or get_settings()
        self._k1 = config.bm25_k1 if k1 is None else k1
        self._b = config.bm25_b if b is None else b
        self._default_top_n = config.bm25_top_n
        self._settings = config
        self._chunks: list[Chunk] = list(chunks)
        self._by_id = {chunk.chunk_id: chunk for chunk in self._chunks}

        # Use config-driven analysis for the corpus, including section title
        # and document title so queries against structural headings still hit
        # the right chunk (CLAUDE.md §7 — BM25 also indexes titles).
        self._corpus = [
            analyze(
                " ".join(
                    part
                    for part in (
                        chunk.text,
                        chunk.section_title or "",
                        str(chunk.metadata.get("title", "")),
                    )
                    if part
                ),
                remove_stopwords=config.bm25_remove_stopwords,
                expand_identifiers=config.bm25_expand_identifiers,
            )
            for chunk in self._chunks
        ]
        self._term_sets = [set(terms) for terms in self._corpus]

        from rank_bm25 import BM25Okapi

        self._bm25: BM25Okapi | None = (
            BM25Okapi(self._corpus, k1=self._k1, b=self._b) if self._corpus else None
        )

    @classmethod
    def from_chunk_file(
        cls, path: Path | None = None, *, settings: Settings | None = None
    ) -> "BM25Index":
        config = settings or get_settings()
        source = path or config.processed_dir / "chunks.jsonl"
        return cls(list(load_chunks(source)), settings=config)

    def __len__(self) -> int:
        return len(self._chunks)

    def get(self, chunk_id: str) -> Chunk | None:
        return self._by_id.get(chunk_id)

    def search(
        self, query: str, user_context: UserContext, top_n: int | None = None
    ) -> list[RankedChunk]:
        limit = self._default_top_n if top_n is None else top_n

        # Use config-driven analysis for the query
        terms = analyze(
            query,
            remove_stopwords=self._settings.bm25_remove_stopwords,
            expand_identifiers=self._settings.bm25_expand_identifiers,
        )

        if self._bm25 is None or not terms or limit <= 0:
            return []

        wanted = set(terms)
        scores = self._bm25.get_scores(terms)
        ordered = sorted(
            (i for i, term_set in enumerate(self._term_sets) if term_set & wanted),
            key=lambda i: (-float(scores[i]), self._chunks[i].chunk_id),
        )

        # Filter for authorization
        authorized_ordered = [
            i for i in ordered if AuthorizationEngine.is_authorized(user_context, self._chunks[i])
        ]

        return [
            RankedChunk(
                chunk=self._chunks[i],
                score=float(scores[i]),
                rank=rank,
                retriever=RETRIEVER_NAME,
            )
            for rank, i in enumerate(authorized_ordered[:limit], start=1)
        ]

    @property
    def stats(self) -> dict[str, object]:
        lengths = [len(terms) for terms in self._corpus]
        vocabulary = {term for terms in self._corpus for term in terms}
        return {
            "chunks": len(self._chunks),
            "documents": len({chunk.document_id for chunk in self._chunks}),
            "vocabulary": len(vocabulary),
            "terms_total": sum(lengths),
            "terms_mean": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
            "k1": self._k1,
            "b": self._b,
        }
