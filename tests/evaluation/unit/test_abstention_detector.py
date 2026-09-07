"""Unit tests for the shared abstention detector.

Guards the single source of truth for "did the model decline to answer".
Before this module three call sites each had their own phrase list, so a
correct decline phrased a fourth way was scored as a failed abstention. These
tests pin the contract the generator and the eval harness both rely on.
"""

from __future__ import annotations

from hybridrag.generation.abstention import ABSTENTION_SENTENCE, looks_like_abstention


def test_canonical_sentence_is_detected() -> None:
    # The exact sentence the prompt tells the model to emit MUST be recognized,
    # or every correct abstention would score as a failure.
    assert looks_like_abstention(ABSTENTION_SENTENCE)


def test_common_paraphrases_are_detected() -> None:
    for answer in (
        "I don't know the answer to that.",
        "The provided documents do not contain information about that.",
        "There is no relevant evidence in the context.",
        "I cannot answer that from the available evidence.",
        "That is outside the scope of the provided documents.",
        "The evidence is insufficient information to answer.",
    ):
        assert looks_like_abstention(answer), answer


def test_real_answers_are_not_flagged() -> None:
    for answer in (
        "The remote work policy allows up to two days per week from home.",
        "Invoices are approved by the finance manager before payment.",
        "Passwords must be at least 12 characters long.",
        "",
    ):
        assert not looks_like_abstention(answer), answer


def test_detection_is_case_insensitive() -> None:
    assert looks_like_abstention("I DO NOT KNOW.")
    assert looks_like_abstention("Insufficient Information Available")
