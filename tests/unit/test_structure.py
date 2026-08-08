"""Unit tests for tokenization and Markdown structure extraction."""

from hybridrag.ingestion import count_tokens, parse_sections, split_paragraphs, split_sentences


class TestTokenization:
    def test_empty_text_is_zero_tokens(self) -> None:
        assert count_tokens("") == 0

    def test_common_words_are_one_token_each(self) -> None:
        # Real WordPiece counts, not an estimate: these five words are all in
        # the vocabulary, so they tokenize 1:1.
        assert count_tokens("one two three four five") == 5

    def test_rare_words_split_into_subword_tokens(self) -> None:
        # The property a word-count heuristic cannot capture, and the reason
        # chunks used to overflow the model's input limit.
        assert count_tokens("unconscionable") > 1

    def test_longer_text_has_more_tokens(self) -> None:
        assert count_tokens("a b c d e f g h") > count_tokens("a b c")

    def test_count_matches_the_configured_embedding_model(self) -> None:
        from hybridrag.config import get_settings
        from hybridrag.ingestion.tokenization import get_tokenizer

        text = "Employees may work remotely up to 2 days per week."
        tokenizer = get_tokenizer(get_settings().embedding_model)
        assert count_tokens(text) == len(tokenizer.tokenize(text))

    def test_paragraphs_split_on_blank_lines(self) -> None:
        assert split_paragraphs("first para\n\nsecond para\n\n\nthird") == [
            "first para",
            "second para",
            "third",
        ]

    def test_paragraph_keeps_list_with_its_lead_in(self) -> None:
        text = "Eligibility criteria:\n- must be confirmed\n- must have internet"
        assert split_paragraphs(text) == [text]

    def test_sentences_split_on_terminal_punctuation(self) -> None:
        parts = split_sentences("First one. Second one! Third one?")
        assert parts == ["First one.", "Second one!", "Third one?"]

    def test_sentence_split_does_not_break_decimals_mid_number(self) -> None:
        # No whitespace after the '.', so no split point.
        assert split_sentences("The limit is 2.5 days per week.") == [
            "The limit is 2.5 days per week."
        ]


class TestParseSections:
    def test_body_without_headings_is_one_untitled_section(self) -> None:
        sections = parse_sections("just some text\n\nand more text")
        assert len(sections) == 1
        assert sections[0].display_title is None

    def test_empty_body_yields_no_sections(self) -> None:
        assert parse_sections("   \n\n  ") == []

    def test_headings_become_separate_sections(self) -> None:
        sections = parse_sections("# Title\n\nintro\n\n## One\n\nalpha\n\n## Two\n\nbeta")
        titles = [s.display_title for s in sections]
        assert titles == ["Title", "Title > One", "Title > Two"]
        assert sections[1].text == "alpha"

    def test_heading_path_pops_on_shallower_heading(self) -> None:
        body = "# A\n\nx\n\n## B\n\ny\n\n### C\n\nz\n\n## D\n\nw"
        paths = [s.display_title for s in parse_sections(body)]
        assert paths == ["A", "A > B", "A > B > C", "A > D"]

    def test_skipped_heading_level_omits_empty_padding(self) -> None:
        # '#' straight to '###' must not produce 'A >  > C'.
        assert parse_sections("# A\n\nx\n\n### C\n\nz")[1].display_title == "A > C"

    def test_headings_inside_code_fences_are_not_structure(self) -> None:
        body = "# Real\n\n```yaml\n# not a heading\nkey: value\n```\n\ntext"
        sections = parse_sections(body)
        assert [s.display_title for s in sections] == ["Real"]
        assert "# not a heading" in sections[0].text

    def test_horizontal_rules_are_dropped(self) -> None:
        sections = parse_sections("# A\n\nalpha\n\n---------------\n\nbeta")
        assert "---" not in sections[0].text
        assert "alpha" in sections[0].text and "beta" in sections[0].text
