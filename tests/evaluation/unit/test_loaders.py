"""Unit tests for loaders, exercised against REAL corpus files.

Using real files (not synthetic fixtures) verifies that normalization
actually handles every frontmatter shape present in data/raw/.
"""

from pathlib import Path

import pytest

from hybridrag.domain import Classification, SourceType
from hybridrag.ingestion import load_file

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="raw corpus not present")


def _load_one(rel_path: str, source_type: SourceType):  # type: ignore[no-untyped-def]
    docs = load_file(RAW / rel_path, source_type, RAW)
    assert len(docs) == 1
    return docs[0]


class TestGenericLoader:
    def test_policy(self) -> None:
        item = _load_one("policies/hr/HR-003_remote_work_policy_v1.md", SourceType.POLICY)
        doc = item.document
        assert doc.document_id == "HR-003"
        assert doc.title == "Remote Work Policy"
        assert doc.classification is Classification.PUBLIC
        assert doc.document_version == "v1"
        assert "employee" in doc.allowed_roles
        assert doc.allowed_departments == ("*",)
        assert doc.source_uri == "raw/policies/hr/HR-003_remote_work_policy_v1.md"
        assert len(doc.checksum) == 64
        assert doc.word_count > 500
        assert doc.estimated_tokens > doc.word_count  # ~1.3 tokens/word
        assert "Remote Work" in item.body

    def test_email_id_field_normalized(self) -> None:
        doc = _load_one("communications/emails/2026-01/EMAIL-001.md", SourceType.EMAIL).document
        assert doc.document_id == "EMAIL-001"  # from email_id frontmatter key
        assert doc.classification is Classification.RESTRICTED
        assert doc.allowed_roles == ("admin",)
        assert doc.owner_user_id == "Arvind Malhotra"  # from 'owner' alias
        assert doc.document_type == "email"

    def test_meeting(self) -> None:
        doc = _load_one("communications/meetings/MTG-001.md", SourceType.MEETING).document
        assert doc.document_id == "MTG-001"
        assert doc.classification is Classification.CONFIDENTIAL
        assert doc.allowed_roles == ("manager", "admin")
        assert "participants" in doc.metadata  # unmapped extras preserved

    def test_jira(self) -> None:
        doc = _load_one("engineering/jira/JIRA-ORION-001.md", SourceType.JIRA).document
        assert doc.document_id == "JIRA-ORION-001"  # from issue_id key
        assert doc.classification is Classification.DEPARTMENT_INTERNAL
        assert doc.department == "ENG"
        assert doc.metadata["related_documents"] == ["ENG-003", "ITSEC-002", "SEC-001"]

    def test_github(self) -> None:
        doc = _load_one("engineering/github/GH-PR-001.md", SourceType.GITHUB).document
        assert doc.document_id == "GH-PR-001"  # from github_id key
        assert "it" in doc.allowed_roles

    def test_checksum_is_reproducible(self) -> None:
        path = "policies/hr/HR-003_remote_work_policy_v1.md"
        first = _load_one(path, SourceType.POLICY).document.checksum
        second = _load_one(path, SourceType.POLICY).document.checksum
        assert first == second


class TestSlackLoader:
    def test_one_document_per_thread_with_own_auth(self) -> None:
        docs = load_file(RAW / "communications/slack/eng-backend.md", SourceType.SLACK, RAW)
        assert len(docs) == 2  # eng-backend.md contains 2 threads
        ids = [d.document.document_id for d in docs]
        assert ids[0] == "SLK-ENG-BE-001"
        # Every thread carries its own authorization metadata.
        for d in docs:
            assert d.document.allowed_roles
            assert d.document.source_type is SourceType.SLACK
            assert d.document.document_type == "slack_thread"

    def test_thread_title_from_heading(self) -> None:
        docs = load_file(RAW / "communications/slack/eng-backend.md", SourceType.SLACK, RAW)
        assert docs[0].document.title == "Authentication Service Failure"
