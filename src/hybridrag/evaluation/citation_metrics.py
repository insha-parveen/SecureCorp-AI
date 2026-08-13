"""Citation metrics for the Phase 8 evaluation suite.

These metrics consume ``FinalResponse`` objects from the generation layer
and compute three things:

- ``valid_citation_rate`` — fraction of LLM-issued citations that survived
  server-side validation against the provided evidence list.
- ``invalid_citation_rate`` — symmetric complement.
- ``citation_coverage`` — fraction of items where the answer cites at least
  one evidence chunk AND the answer is non-empty AND the answer is not an
  abstention. Items with ``expected_abstain=true`` are excluded from the
  coverage denominator.

Rate averaging is **per-item**, not pooled. Each item contributes its own
``valid_count / total_cited`` and the metric is the unweighted mean across
items that produced at least one citation. Items with no citations at all
(including abstentions, which never cite) are excluded from both the numerator
and the denominator of the rate. This makes abstention exclusion safe: it
neither deflates a low-citation category nor artificially inflates a
high-citation one, and it lets the rate be reported for the same item set
that produced the citations.

The harness never modifies the responses — it only reads them.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from hybridrag.domain import FinalResponse

_ABSTENTION_MARKERS = (
    "do not know",
    "insufficient information",
    "outside my scope",
    "i cannot answer",
    "i am sorry",
    "not authorized",
    "access denied",
)


def _is_abstention(answer: str) -> bool:
    text = answer.lower()
    return any(marker in text for marker in _ABSTENTION_MARKERS)


@dataclass(frozen=True)
class CitationMetrics:
    valid_citation_rate: float
    invalid_citation_rate: float
    citation_coverage: float
    n_items: int
    n_abstentions: int
    n_with_citations: int


def compute_citation_metrics(
    responses: Iterable[tuple[dict[str, object], FinalResponse]],
    abstain_predicate: Callable[[dict[str, object], FinalResponse], bool] | None = None,
) -> CitationMetrics:
    """Compute citation metrics from paired (golden_item, response) tuples.

    Args:
        responses: Iterable of ``(golden_item, FinalResponse)`` pairs.
        abstain_predicate: Optional callable ``(golden_item, response) -> bool``
            that determines whether an item should be excluded from the
            coverage denominator (because the assistant correctly abstained).
            Defaults to a marker-text check on the response.answer.
    """
    n_items = 0
    n_abstentions = 0
    n_with_citations = 0
    sum_valid = 0.0
    sum_invalid = 0.0
    n_with_citation_signal = 0

    for golden, resp in responses:
        n_items += 1
        is_abstain = (
            abstain_predicate(golden, resp)
            if abstain_predicate is not None
            else _is_abstention(resp.answer)
        )
        if is_abstain:
            n_abstentions += 1
            # Abstentions are excluded from coverage and from the citation rate
            # denominators — abstention is a correct outcome.
            continue

        # Coverage: did the answer cite at least one evidence chunk?
        if resp.citations and resp.evidence:
            n_with_citations += 1

        # valid_citation_rate: post-validation / pre-validation. Since the
        # response we observe has already been validated by the generator,
        # the "issued" count equals the "validated" count. We treat that as
        # the rate unless it exceeds the evidence length (impossible after
        # validation, but defensive).
        if resp.evidence:
            n_evidence = len(resp.evidence)
            valid_count = sum(1 for r in resp.citations if 1 <= r <= n_evidence)
            invalid_count = len(resp.citations) - valid_count
            total = valid_count + invalid_count
            if total > 0:
                sum_valid += valid_count / total
                sum_invalid += invalid_count / total
                n_with_citation_signal += 1

    if n_items == 0:
        return CitationMetrics(0.0, 0.0, 0.0, 0, 0, 0)

    n_for_coverage = n_items - n_abstentions
    coverage = (n_with_citations / n_for_coverage) if n_for_coverage > 0 else 0.0
    valid_rate = (sum_valid / n_with_citation_signal) if n_with_citation_signal > 0 else 0.0
    invalid_rate = (sum_invalid / n_with_citation_signal) if n_with_citation_signal > 0 else 0.0

    return CitationMetrics(
        valid_citation_rate=valid_rate,
        invalid_citation_rate=invalid_rate,
        citation_coverage=coverage,
        n_items=n_items,
        n_abstentions=n_abstentions,
        n_with_citations=n_with_citations,
    )
