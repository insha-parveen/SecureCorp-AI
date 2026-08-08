"""Document registry: walk the raw corpus, validate it, persist a JSONL manifest.

Responsibilities:

- classify each raw file's source family from its *directory* (the corpus's
  frontmatter ``source_type`` values are inconsistent — ``generated``,
  ``google_drive``, even ``jira ✅`` — so the path is the reliable signal);
- load every file through the loaders into normalized Documents;
- validate the resulting corpus (duplicate IDs, fail-closed auth defaults,
  ID-format deviations) and *report* problems instead of silently fixing them;
- persist ``data/processed/registry.jsonl`` (one Document per line, sorted,
  reproducible) plus ``registry_issues.jsonl`` for the validation report.

The registry is the single manifest the chunking and indexing layers consume.
"""

import json
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel

from hybridrag.domain import Document, SourceType
from hybridrag.ingestion.loaders import LoadedDocument, load_file

# Directory (relative to data/raw/) → source family. Order matters only for
# readability; lookup matches the deepest prefix.
SOURCE_DIRS: dict[str, SourceType] = {
    "policies": SourceType.POLICY,
    "knowledge_base": SourceType.KNOWLEDGE_BASE,
    "communications/emails": SourceType.EMAIL,
    "communications/meetings": SourceType.MEETING,
    "communications/slack": SourceType.SLACK,
    "engineering/jira": SourceType.JIRA,
    "engineering/github": SourceType.GITHUB,
}

# Company Bible §5 ID conventions per family (deviations are warnings, not
# errors — e.g. the EMAIL-2026-0001 variant exists in the corpus).
_ID_PATTERNS: dict[SourceType, re.Pattern[str]] = {
    SourceType.POLICY: re.compile(r"^(HR|FIN|ITSEC)-\d{3}$"),
    SourceType.KNOWLEDGE_BASE: re.compile(r"^[A-Z]+-\d{3}$"),
    SourceType.EMAIL: re.compile(r"^EMAIL-\d{3}$"),
    SourceType.MEETING: re.compile(r"^MTG-\d{3}$"),
    SourceType.SLACK: re.compile(r"^SLK-[A-Z0-9-]+$"),
    SourceType.JIRA: re.compile(r"^JIRA-[A-Z]+-\d{3}$"),
    SourceType.GITHUB: re.compile(r"^GH-(ISS|PR|DISC)-\d{3}$"),
}


class ValidationIssue(BaseModel):
    """One corpus problem found during ingestion (reported, never hidden)."""

    severity: str  # "error" | "warning"
    source_uri: str
    document_id: str | None = None
    message: str


class DocumentRegistry:
    """In-memory corpus manifest with JSONL persistence."""

    def __init__(
        self, documents: list[LoadedDocument], issues: list[ValidationIssue] | None = None
    ) -> None:
        self._loaded = documents
        self._by_id: dict[str, LoadedDocument] = {}
        self.issues: list[ValidationIssue] = list(issues or [])
        for item in documents:
            doc_id = item.document.document_id
            if doc_id in self._by_id:
                self.issues.append(
                    ValidationIssue(
                        severity="error",
                        source_uri=item.document.source_uri,
                        document_id=doc_id,
                        message=f"duplicate document_id (also in "
                        f"{self._by_id[doc_id].document.source_uri})",
                    )
                )
            else:
                self._by_id[doc_id] = item

    # --- construction ---

    @classmethod
    def build(cls, raw_dir: Path) -> "DocumentRegistry":
        """Walk ``data/raw/`` and load every corpus Markdown file.

        Skips ``_``-prefixed files (corpus-generation validation reports) and
        anything outside the known source directories (e.g. ``structured/``
        CSVs, which belong to the SQL path, not document RAG).
        """
        loaded: list[LoadedDocument] = []
        issues: list[ValidationIssue] = []
        for path in sorted(raw_dir.rglob("*.md")):
            if path.name.startswith("_"):
                continue
            source_type = _classify(path, raw_dir)
            if source_type is None:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source_uri=path.relative_to(raw_dir.parent).as_posix(),
                        message="file is outside known source directories; skipped",
                    )
                )
                continue
            docs = load_file(path, source_type, raw_dir)
            if not docs:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source_uri=path.relative_to(raw_dir.parent).as_posix(),
                        message="file yielded no documents",
                    )
                )
            loaded.extend(docs)
        registry = cls(loaded, issues)
        registry.validate()
        return registry

    # --- validation ---

    def validate(self) -> list[ValidationIssue]:
        """Run corpus-level checks; append findings to ``self.issues``."""
        for item in self._loaded:
            doc = item.document
            for field in doc.metadata.get("_defaults_applied", []):
                self._warn(doc, f"'{field}' missing in frontmatter; fail-closed default applied")
            pattern = _ID_PATTERNS.get(doc.source_type)
            if pattern and not pattern.match(doc.document_id):
                self._warn(
                    doc,
                    f"document_id '{doc.document_id}' deviates from the "
                    f"{doc.source_type.value} naming convention",
                )
            if not item.body.strip():
                self._warn(doc, "document body is empty")
        return self.issues

    def _warn(self, doc: Document, message: str) -> None:
        self.issues.append(
            ValidationIssue(
                severity="warning",
                source_uri=doc.source_uri,
                document_id=doc.document_id,
                message=message,
            )
        )

    # --- access ---

    @property
    def documents(self) -> list[LoadedDocument]:
        return list(self._loaded)

    def get(self, document_id: str) -> LoadedDocument | None:
        return self._by_id.get(document_id)

    def __len__(self) -> int:
        return len(self._loaded)

    def stats(self) -> dict[str, int]:
        """Per-source-type document counts (for reporting and tests)."""
        counts = Counter(item.document.source_type.value for item in self._loaded)
        return dict(sorted(counts.items()))

    # --- persistence (JSONL: one Document per line, deterministic order) ---

    def save(self, processed_dir: Path) -> tuple[Path, Path]:
        """Write ``registry.jsonl`` and ``registry_issues.jsonl``.

        Bodies are NOT persisted — the registry is a metadata manifest; the
        chunking layer re-reads raw files via ``source_uri`` (raw data stays
        the single source of truth).
        """
        processed_dir.mkdir(parents=True, exist_ok=True)
        registry_path = processed_dir / "registry.jsonl"
        issues_path = processed_dir / "registry_issues.jsonl"
        with registry_path.open("w", encoding="utf-8") as fh:
            for item in sorted(self._loaded, key=lambda x: x.document.document_id):
                fh.write(json.dumps(item.document.model_dump(mode="json"), sort_keys=True) + "\n")
        with issues_path.open("w", encoding="utf-8") as fh:
            for issue in self.issues:
                fh.write(json.dumps(issue.model_dump(mode="json"), sort_keys=True) + "\n")
        return registry_path, issues_path

    @staticmethod
    def load_documents(registry_path: Path) -> Iterator[Document]:
        """Stream Documents back from a saved ``registry.jsonl``."""
        with registry_path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield Document.model_validate(json.loads(line))


def _classify(path: Path, raw_dir: Path) -> SourceType | None:
    """Map a file's directory (relative to data/raw/) to its source family."""
    rel = path.relative_to(raw_dir).as_posix()
    for prefix, source_type in SOURCE_DIRS.items():
        if rel.startswith(prefix + "/"):
            return source_type
    return None
