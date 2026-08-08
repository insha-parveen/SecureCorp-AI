"""Unit tests for document-type-aware chunking.

Synthetic bodies cover the packing/boundary rules precisely; real corpus files
verify the strategies actually fit the shapes present in data/raw/.
"""

from datetime import date
from pathlib import Path

import pytest

from hybridrag.domain import Chunk, Classification, Document, SourceType
from hybridrag.ingestion import atomize, chunk_document, load_file

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

needs_corpus = pytest.mark.skipif(not RAW.exists(), reason="raw corpus not present")

# Small budgets keep synthetic fixtures readable while exercising real logic.
SMALL = {"target_tokens": 40, "max_tokens": 60, "overlap_tokens": 10}
# Mirrors the configured production budget so corpus tests exercise real sizes.
LARGE = {"target_tokens": 440, "max_tokens": 440, "overlap_tokens": 60}


def _doc(**overrides: object) -> Document:
    base: dict[str, object] = {
        "document_id": "HR-003",
        "title": "Remote Work Policy",
        "source_type": SourceType.POLICY,
        "document_type": "policy",
        "department": "HR",
        "classification": Classification.PUBLIC,
        "allowed_roles": ("employee", "hr"),
        "allowed_departments": ("*",),
        "document_version": "v1",
        "effective_date": date(2025, 1, 1),
        "source_uri": "raw/policies/hr/HR-003_remote_work_policy_v1.md",
        "checksum": "0" * 64,
    }
    return Document(**{**base, **overrides})  # type: ignore[arg-type]


def _words(n: int, word: str = "word") -> str:
    return " ".join([word] * n)


class TestChunkIdentityAndMetadata:
    def test_chunk_ids_are_stable_sequential_and_unique(self) -> None:
        body = "# A\n\n" + "\n\n".join(_words(40) for _ in range(6))
        chunks = chunk_document(_doc(), body, **SMALL)  # type: ignore[arg-type]
        assert len(chunks) > 1
        assert [c.chunk_id for c in chunks] == [f"HR-003:v1:{i:04d}" for i in range(len(chunks))]
        assert len({c.chunk_id for c in chunks}) == len(chunks)

    def test_chunking_is_deterministic(self) -> None:
        body = "# A\n\n" + "\n\n".join(_words(30) for _ in range(8))
        first = chunk_document(_doc(), body, **SMALL)  # type: ignore[arg-type]
        second = chunk_document(_doc(), body, **SMALL)  # type: ignore[arg-type]
        assert [c.model_dump() for c in first] == [c.model_dump() for c in second]

    def test_version_is_part_of_the_chunk_id(self) -> None:
        body = "# A\n\nsome text"
        v2 = chunk_document(_doc(document_version="v2"), body, **SMALL)  # type: ignore[arg-type]
        assert v2[0].chunk_id == "HR-003:v2:0000"

    def test_authorization_metadata_is_inherited_verbatim(self) -> None:
        doc = _doc(
            classification=Classification.CONFIDENTIAL,
            allowed_roles=("hr", "admin"),
            allowed_departments=("HR",),
            owner_user_id="EMP-0104",
        )
        body = "# A\n\n" + "\n\n".join(_words(40) for _ in range(5))
        chunks = chunk_document(doc, body, **SMALL)  # type: ignore[arg-type]
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.classification is Classification.CONFIDENTIAL
            assert chunk.allowed_roles == ("hr", "admin")
            assert chunk.allowed_departments == ("HR",)
            assert chunk.owner_user_id == "EMP-0104"
            assert chunk.tenant_id == doc.tenant_id
            assert chunk.department == doc.department
            assert chunk.effective_date == doc.effective_date

    def test_content_hash_matches_text(self) -> None:
        chunks = chunk_document(_doc(), "# A\n\nhello world", **SMALL)  # type: ignore[arg-type]
        assert len(chunks[0].content_hash) == 64
        differing = chunk_document(_doc(), "# A\n\nhello there", **SMALL)  # type: ignore[arg-type]
        assert chunks[0].content_hash != differing[0].content_hash

    def test_empty_body_yields_no_chunks(self) -> None:
        assert chunk_document(_doc(), "   \n\n ", **SMALL) == []  # type: ignore[arg-type]


class TestPackingAndBoundaries:
    def test_small_document_becomes_a_single_chunk(self) -> None:
        chunks = chunk_document(_doc(), "# A\n\nshort body text", **LARGE)  # type: ignore[arg-type]
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0

    def test_chunks_respect_the_max_token_budget(self) -> None:
        body = "# A\n\n" + "\n\n".join(_words(25) for _ in range(20))
        for chunk in chunk_document(_doc(), body, **SMALL):  # type: ignore[arg-type]
            assert chunk.token_count <= SMALL["max_tokens"] + SMALL["overlap_tokens"]

    def test_section_change_ends_a_chunk_once_it_is_big_enough(self) -> None:
        body = "## One\n\n" + _words(200, "alpha") + "\n\n## Two\n\n" + _words(200, "beta")
        chunks = chunk_document(
            _doc(), body, target_tokens=550, max_tokens=700, overlap_tokens=75, min_tokens=100
        )
        assert len(chunks) == 2
        assert "beta" not in chunks[0].text
        assert "alpha" not in chunks[1].text

    def test_small_adjacent_sections_merge_instead_of_fragmenting(self) -> None:
        # Heading-dense documents must not yield a swarm of tiny chunks.
        body = "\n\n".join(f"## S{i}\n\ncontent for section {i}" for i in range(8))
        chunks = chunk_document(
            _doc(), body, target_tokens=550, max_tokens=700, overlap_tokens=0, min_tokens=200
        )
        assert len(chunks) == 1
        assert chunks[0].metadata["section_titles"] == [f"S{i}" for i in range(8)]
        assert chunks[0].section_title == "S0"

    def test_merging_stops_at_the_target_budget(self) -> None:
        body = "\n\n".join(f"## S{i}\n\n" + _words(60) for i in range(10))
        chunks = chunk_document(
            _doc(), body, target_tokens=200, max_tokens=300, overlap_tokens=0, min_tokens=150
        )
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= 300

    def test_section_title_is_recorded_as_the_heading_trail(self) -> None:
        body = "# Remote Work Policy\n\nintro\n\n## 3. Framework\n\n### 3.1 Limit\n\nmax 2 days"
        chunks = chunk_document(_doc(), body, **LARGE)  # type: ignore[arg-type]
        titles = [c.section_title for c in chunks]
        assert "Remote Work Policy > 3. Framework > 3.1 Limit" in titles

    def test_overlap_carries_context_within_a_section(self) -> None:
        # Overlap works at atom granularity: a trailing paragraph is carried
        # forward only if it fits the overlap budget, so the paragraphs here
        # are deliberately smaller than overlap_tokens.
        paragraphs = [f"para{i} " + _words(6) for i in range(10)]
        body = "# A\n\n" + "\n\n".join(paragraphs)
        chunks = chunk_document(_doc(), body, target_tokens=40, max_tokens=60, overlap_tokens=15)
        assert len(chunks) > 1
        # The last paragraph of chunk N must reappear at the start of chunk N+1.
        assert any(
            chunks[i + 1].text.startswith(chunks[i].text.split("\n\n")[-1])
            for i in range(len(chunks) - 1)
        ), "expected a carried-over paragraph between consecutive in-section chunks"

    def test_no_overlap_when_paragraphs_exceed_the_overlap_budget(self) -> None:
        # A paragraph larger than overlap_tokens is never partially carried,
        # so chunks stay disjoint rather than duplicating a whole paragraph.
        body = "# A\n\n" + "\n\n".join(f"para{i} " + _words(30) for i in range(4))
        chunks = chunk_document(_doc(), body, target_tokens=40, max_tokens=60, overlap_tokens=10)
        assert len(chunks) > 1
        markers = [
            marker
            for chunk in chunks
            for marker in ("para0", "para1", "para2", "para3")
            if marker in chunk.text
        ]
        assert len(markers) == len(set(markers)), "no paragraph should appear twice"

    def test_overlap_never_duplicates_text_across_a_section_boundary(self) -> None:
        body = "## One\n\n" + _words(45, "alpha") + "\n\n## Two\n\n" + _words(45, "beta")
        chunks = chunk_document(
            _doc(), body, target_tokens=40, max_tokens=60, overlap_tokens=15, min_tokens=0
        )
        # The section-Two chunks must not repeat any section-One text.
        for chunk in chunks:
            if "beta" in chunk.text:
                assert "alpha" not in chunk.text

    def test_oversized_paragraph_is_split_on_sentences(self) -> None:
        giant = " ".join(f"Sentence number {i} has some filler words." for i in range(40))
        chunks = chunk_document(_doc(), f"# A\n\n{giant}", **SMALL)  # type: ignore[arg-type]
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= SMALL["max_tokens"] + SMALL["overlap_tokens"]

    def test_numbered_procedure_stays_in_one_chunk(self) -> None:
        body = "## Workflow\n\n1. Submit request.\n2. Manager reviews.\n3. HR approves."
        chunks = chunk_document(_doc(), body, **LARGE)  # type: ignore[arg-type]
        assert len(chunks) == 1
        for step in ("1. Submit", "2. Manager", "3. HR"):
            assert step in chunks[0].text


class TestAtomizerSelection:
    def test_conversation_atomizer_merges_speaker_attribution(self) -> None:
        body = "# Transcript\n\n**10:00**\n**Sunita Rao:**\n\nWe moved to hybrid search.\n\n"
        atoms = atomize(body, SourceType.MEETING)
        speaker_atoms = [a for a in atoms if "Sunita Rao" in a.text]
        assert speaker_atoms, "speaker attribution should survive atomization"
        assert "hybrid search" in speaker_atoms[0].text

    def test_email_atoms_share_one_boundary(self) -> None:
        body = "# Subject line\n\n**From:** A\n\n**Body:**\n\nHello team.\n\nRegards."
        assert {a.boundary_key for a in atomize(body, SourceType.EMAIL)} == {"document"}

    def test_policy_atoms_are_scoped_per_section(self) -> None:
        body = "## One\n\nalpha\n\n## Two\n\nbeta"
        assert len({a.boundary_key for a in atomize(body, SourceType.POLICY)}) == 2


@needs_corpus
class TestRealCorpus:
    def _chunks(self, rel_path: str, source_type: SourceType) -> list[Chunk]:
        loaded = load_file(RAW / rel_path, source_type, RAW)
        return [
            c
            for item in loaded
            for c in chunk_document(item.document, item.body, **LARGE)  # type: ignore[arg-type]
        ]

    def test_policy_chunks_carry_section_titles(self) -> None:
        chunks = self._chunks("policies/hr/HR-003_remote_work_policy_v1.md", SourceType.POLICY)
        assert len(chunks) > 1
        assert all(c.section_title for c in chunks)
        assert all(c.document_id == "HR-003" for c in chunks)

    def test_remote_work_limit_is_retrievable_in_one_chunk(self) -> None:
        # The canonical eval question "What is the remote work weekly limit?"
        # must have its answer intact inside a single chunk.
        chunks = self._chunks("policies/hr/HR-003_remote_work_policy_v1.md", SourceType.POLICY)
        assert any("2 days per week" in c.text for c in chunks)

    def test_short_email_stays_one_chunk(self) -> None:
        chunks = self._chunks("communications/emails/2026-01/EMAIL-001.md", SourceType.EMAIL)
        assert len(chunks) == 1
        assert "Subject:" in chunks[0].text

    def test_slack_file_yields_chunks_per_independent_thread(self) -> None:
        chunks = self._chunks("communications/slack/hr.md", SourceType.SLACK)
        assert len({c.document_id for c in chunks}) > 1
        # Every thread's chunks keep that thread's own authorization.
        for chunk in chunks:
            assert chunk.allowed_roles

    def test_meeting_transcript_chunks_stay_within_budget(self) -> None:
        chunks = self._chunks("communications/meetings/MTG-001.md", SourceType.MEETING)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count <= LARGE["max_tokens"] + LARGE["overlap_tokens"]

    def test_jira_issue_sections_are_preserved(self) -> None:
        chunks = self._chunks("engineering/jira/JIRA-ORION-001.md", SourceType.JIRA)
        text = " ".join(c.text for c in chunks)
        assert "Steps to Reproduce" in text or any(
            c.section_title and "Steps to Reproduce" in c.section_title for c in chunks
        )
