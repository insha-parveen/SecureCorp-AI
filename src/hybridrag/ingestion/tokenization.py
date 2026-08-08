"""Token counting and text splitting primitives used by the chunking layer.

Token counting is the embedding model's OWN tokenizer, loaded through
``transformers.AutoTokenizer``. This is not a detail: a chunk that exceeds the
model's ``max_seq_length`` is silently truncated at encode time, so the tail of
that chunk never reaches the index and can never be retrieved — with no error
and no warning. Sizing chunks with an approximation therefore loses evidence
invisibly, which is exactly what the earlier ~1.3-tokens-per-word heuristic did:
it undercounted by ~1.28x on this corpus and pushed 64 of 387 chunks past the
MiniLM 512-token limit.

Counting stays behind one function so the chunker never touches a tokenizer
directly, and so swapping the embedding model automatically re-sizes chunks.

The splitters are format-level helpers with no knowledge of Document/Chunk.
"""

import re
from functools import lru_cache
from typing import TYPE_CHECKING

from hybridrag.config import get_settings

if TYPE_CHECKING:  # pragma: no cover - typing only
    from transformers import PreTrainedTokenizerBase

# Blank-line separated blocks. A "paragraph" here includes a bullet/numbered
# list written as consecutive lines, which is what we want: splitting a list
# away from its lead-in sentence destroys the meaning of a policy clause.
_PARAGRAPH_RE = re.compile(r"\n\s*\n")

# Sentence boundary: punctuation followed by whitespace and a capital/quote/digit.
# Deliberately conservative — over-splitting is worse than under-splitting here,
# because sentences are only used as a fallback for oversized paragraphs.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[0-9])")


@lru_cache(maxsize=4)
def get_tokenizer(model_name: str) -> "PreTrainedTokenizerBase":
    """Load (and cache) the tokenizer for ``model_name``.

    Cached because chunking calls ``count_tokens`` thousands of times per run.
    Only the tokenizer is loaded, never the model weights, so this is cheap.
    """
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(model_name)


@lru_cache(maxsize=1)
def _default_tokenizer() -> "PreTrainedTokenizerBase":
    return get_tokenizer(get_settings().embedding_model)


def count_tokens(text: str, model_name: str | None = None) -> int:
    """Exact token count of ``text`` under the embedding model's tokenizer.

    Special tokens are excluded: the caller budgets for them via
    ``Settings.embedding_max_tokens``, which already reserves that headroom.
    """
    tokenizer = get_tokenizer(model_name) if model_name else _default_tokenizer()
    # ``tokenize`` rather than ``encode``: it does not emit the "sequence longer
    # than max length" warning, which is expected here — measuring an oversized
    # block is precisely how the chunker decides to split it.
    return len(tokenizer.tokenize(text))


def split_paragraphs(text: str) -> list[str]:
    """Split text into non-empty, stripped blank-line-separated blocks."""
    return [block for raw in _PARAGRAPH_RE.split(text) if (block := raw.strip())]


def split_sentences(text: str) -> list[str]:
    """Split a block into sentences, falling back to lines for list-shaped text.

    Only used when a single paragraph exceeds the hard chunk limit and must be
    broken up regardless of structure.
    """
    parts: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        parts.extend(piece for s in _SENTENCE_RE.split(stripped) if (piece := s.strip()))
    return parts
