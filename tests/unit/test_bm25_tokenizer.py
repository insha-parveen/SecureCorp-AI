"""Unit tests for the BM25 analyzer.

The analyzer is where BM25 recall is won or lost, so these tests pin the
behaviours the enterprise corpus depends on: compound identifiers survive whole,
their parts are also emitted, and the query side is analyzed identically to the
document side.
"""

from hybridrag.indexing.bm25_store import analyze, STOPWORDS


class TestIdentifiers:
    def test_compound_identifier_survives_as_one_token(self) -> None:
        # The whole identifier is the rare, high-IDF term that makes an exact
        # paste of "INV-2026-0108" rank its own chunk first.
        assert "inv-2026-0108" in analyze("Invoice INV-2026-0108 is overdue")

    def test_compound_identifier_also_emits_its_parts(self) -> None:
        tokens = analyze("INV-2026-0108")
        assert tokens == ["inv-2026-0108", "inv", "2026", "0108"]

    def test_part_expansion_can_be_disabled(self) -> None:
        assert analyze("INV-2026-0108", expand_identifiers=False) == ["inv-2026-0108"]

    def test_underscore_identifiers_split_too(self) -> None:
        assert analyze("ticket_inc_1042") == ["ticket_inc_1042", "ticket", "inc", "1042"]

    def test_partial_identifier_query_shares_a_term_with_the_full_one(self) -> None:
        document = set(analyze("Invoice INV-2026-0108 total is 42,000 INR"))
        assert set(analyze("invoice 0108")) & document


class TestNoise:
    def test_markdown_punctuation_is_dropped(self) -> None:
        assert analyze("## **Remote Work** | policy") == ["remote", "work", "policy"]

    def test_single_characters_are_dropped(self) -> None:
        assert analyze("a b see 1 2 42") == ["see", "42"]

    def test_stopwords_are_removed_by_default(self) -> None:
        tokens = analyze("what is the remote work policy")
        assert tokens == ["remote", "work", "policy"]
        assert not set(tokens) & STOPWORDS

    def test_stopword_removal_can_be_disabled(self) -> None:
        assert "the" in analyze("what is the policy", remove_stopwords=False)

    def test_it_department_is_not_treated_as_a_stopword(self) -> None:
        assert "it" in analyze("escalate to IT security", remove_stopwords=False)
        assert "it" not in STOPWORDS


class TestContract:
    def test_term_frequency_is_preserved(self) -> None:
        assert analyze("expense expense expense report") == [
            "expense",
            "expense",
            "expense",
            "report",
        ]

    def test_order_is_preserved(self) -> None:
        assert analyze("alpha beta gamma") == ["alpha", "beta", "gamma"]

    def test_empty_and_punctuation_only_text_yield_no_terms(self) -> None:
        assert analyze("") == []
        assert analyze("### --- ***") == []

    def test_analysis_is_symmetric_between_query_and_document(self) -> None:
        text = "Expense claim EXP-0042 filed by EMP-0104"
        assert analyze(text.lower()) == analyze(text.upper())
