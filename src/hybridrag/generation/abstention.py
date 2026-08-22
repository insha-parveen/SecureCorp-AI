"""Canonical abstention text and detection — one source of truth.

Before this module, three places each had their OWN idea of what an abstention
looks like: the generation prompt told the model to "state that you do not
know", ``RAGGenerator._is_abstention`` matched one phrase list, and
``evaluation/ragas_runner`` matched a DIFFERENT phrase list. So a model that
correctly declined but phrased it a fourth way was scored as a failed
abstention — depressing the measured abstention_recall even when behaviour was
correct. Everything now routes through here.
"""

from __future__ import annotations

# The exact sentence the model is instructed to emit when the evidence does not
# answer the question. Keeping it fixed makes abstention detection reliable and
# gives the UI a stable string to render distinctly. It contains the marker
# phrase "i do not know" so ``looks_like_abstention`` matches it.
ABSTENTION_SENTENCE = (
    "I do not know — the available documents do not contain enough information "
    "to answer this question."
)

# Substrings (lower-cased) that mark an answer as an abstention. Superset of the
# canonical sentence so a paraphrased decline still counts. Kept deliberately
# specific: generic apologies alone should NOT read as abstention, only phrases
# that actually signal "no answer in the evidence".
_ABSTENTION_MARKERS: tuple[str, ...] = (
    "i do not know",
    "i don't know",
    "do not contain enough information",
    "does not contain enough information",
    "do not contain information",
    "does not contain information",
    "not contain the information",
    "no relevant evidence",
    "not in the evidence",
    "not found in the evidence",
    "insufficient information",
    "cannot answer",
    "can't answer",
    "unable to answer",
    "outside my scope",
    "outside the scope",
)


def looks_like_abstention(answer: str) -> bool:
    """True when ``answer`` reads as a decline-to-answer.

    Pure string check on the answer text — no evidence argument, so it means
    exactly one thing everywhere it is used and cannot drift between the
    generator and the evaluation harness.
    """
    lowered = answer.lower()
    return any(marker in lowered for marker in _ABSTENTION_MARKERS)
