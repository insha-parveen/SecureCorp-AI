"""Unit tests for the DocumentRegistry (full-corpus walk + JSONL round-trip)."""

import json
from pathlib import Path

import pytest

from hybridrag.domain import Document
from hybridrag.ingestion import DocumentRegistry

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="raw corpus not present")


@pytest.fixture(scope="module")
def registry() -> DocumentRegistry:
    return DocumentRegistry.build(RAW)


class TestBuild:
    def test_all_source_types_present(self, registry: DocumentRegistry) -> None:
        stats = registry.stats()
        assert set(stats) == {
            "policy",
            "knowledge_base",
            "email",
            "meeting",
            "slack",
            "jira",
            "github",
        }
        assert stats["policy"] == 19
        assert stats["knowledge_base"] == 11  # 10 original + ABOUT-001 company overview
        assert stats["meeting"] == 12
        assert stats["slack"] == 27  # threads, not files (10 files)
        assert stats["jira"] == 25
        assert stats["github"] == 20
        assert stats["email"] == 162

    def test_validation_reports_are_skipped(self, registry: DocumentRegistry) -> None:
        assert all("_validation_report" not in d.document.source_uri for d in registry.documents)

    def test_no_duplicate_ids(self, registry: DocumentRegistry) -> None:
        duplicates = [i for i in registry.issues if "duplicate document_id" in i.message]
        assert duplicates == []

    def test_every_document_has_auth_metadata(self, registry: DocumentRegistry) -> None:
        for item in registry.documents:
            assert item.document.allowed_roles, item.document.document_id
            assert item.document.classification

    def test_lookup_by_id(self, registry: DocumentRegistry) -> None:
        item = registry.get("HR-003")
        assert item is not None
        assert item.document.title == "Remote Work Policy"


class TestPersistence:
    def test_jsonl_round_trip(self, registry: DocumentRegistry, tmp_path: Path) -> None:
        registry_path, issues_path = registry.save(tmp_path)
        assert registry_path.name == "registry.jsonl"
        assert issues_path.exists()
        reloaded = list(DocumentRegistry.load_documents(registry_path))
        assert len(reloaded) == len(registry)
        assert all(isinstance(d, Document) for d in reloaded)
        # Round-trip preserves a known document exactly.
        original = registry.get("HR-003")
        assert original is not None
        restored = next(d for d in reloaded if d.document_id == "HR-003")
        assert restored == original.document

    def test_output_is_deterministic(self, registry: DocumentRegistry, tmp_path: Path) -> None:
        path_a, _ = registry.save(tmp_path / "a")
        path_b, _ = registry.save(tmp_path / "b")
        assert path_a.read_text(encoding="utf-8") == path_b.read_text(encoding="utf-8")

    def test_lines_are_valid_json(self, registry: DocumentRegistry, tmp_path: Path) -> None:
        registry_path, _ = registry.save(tmp_path)
        with registry_path.open(encoding="utf-8") as fh:
            for line in fh:
                record = json.loads(line)
                assert {"document_id", "checksum", "word_count", "estimated_tokens"} <= set(record)
