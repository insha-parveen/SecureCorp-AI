"""Loaders: raw corpus file → normalized ``Document`` object(s) + body text.

Design (kept deliberately simple):

- ``load_generic``: ONE loader for every standard frontmatter document
  (policies, knowledge base, emails, meetings, jira, github). The families
  differ only in which frontmatter key holds the ID (``document_id`` /
  ``email_id`` / ``meeting_id`` / ``issue_id`` / ``github_id``) and where the
  title comes from — differences small enough for a lookup list, not six
  separate loader functions.
- ``load_slack``: the ONLY dedicated loader. A Slack export holds several
  threads per file, each with its own ``classification``/``allowed_roles``,
  so one file must yield multiple independently-authorized Documents
  (required for the "zero unauthorized chunks" invariant).

Normalization is fail-closed: if a file is missing ``classification`` or
``allowed_roles``, the Document defaults to RESTRICTED / admin-only rather
than public. The registry layer reports these as validation issues.
"""

import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from hybridrag.domain import Classification, Document, DocumentStatus, SourceType
from hybridrag.ingestion.frontmatter import parse_frontmatter, split_slack_threads

# Frontmatter keys that may hold the document's canonical ID, in priority order.
_ID_KEYS = ("document_id", "email_id", "meeting_id", "issue_id", "github_id", "thread_id")

# Default document_type per source family, used when frontmatter has none.
_DEFAULT_DOC_TYPE: dict[SourceType, str] = {
    SourceType.POLICY: "policy",
    SourceType.KNOWLEDGE_BASE: "knowledge_base",
    SourceType.EMAIL: "email",
    SourceType.MEETING: "meeting_transcript",
    SourceType.SLACK: "slack_thread",
    SourceType.JIRA: "issue",
    SourceType.GITHUB: "github_artifact",
}

_HEADING_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_SUBJECT_RE = re.compile(r"^\*{0,2}Subject:\*{0,2}\s*(?P<title>.+?)\s*$", re.MULTILINE)

_TOKENS_PER_WORD = 1.3  # coarse heuristic; real tokenization happens at chunking/eval time


class LoadedDocument(BaseModel):
    """A normalized ``Document`` paired with its Markdown body.

    ``Document`` is pure metadata; the body is carried alongside so the
    future chunking layer can consume text without re-reading and
    re-parsing raw files.
    """

    model_config = ConfigDict(frozen=True)

    document: Document
    body: str


def load_file(path: Path, source_type: SourceType, raw_root: Path) -> list[LoadedDocument]:
    """Load one raw corpus file into one or more normalized Documents.

    Dispatches to the Slack loader for Slack exports and the generic loader
    for everything else. ``raw_root``'s parent is used to compute a
    repo-relative ``source_uri``.
    """
    text = path.read_text(encoding="utf-8")
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    source_uri = path.relative_to(raw_root.parent).as_posix()
    if source_type is SourceType.SLACK:
        return load_slack(text, checksum=checksum, source_uri=source_uri)
    loaded = load_generic(
        text, source_type=source_type, checksum=checksum, source_uri=source_uri, stem=path.stem
    )
    return [loaded]


def load_generic(
    text: str, *, source_type: SourceType, checksum: str, source_uri: str, stem: str
) -> LoadedDocument:
    """Normalize any standard single-document frontmatter file."""
    meta, body = parse_frontmatter(text)
    doc_id = _first_present(meta, _ID_KEYS) or stem
    title = (
        _clean_str(meta.get("title"))
        or _first_match(_HEADING_RE, body)
        or _first_match(_SUBJECT_RE, body)
        or stem
    )
    document = _build_document(
        meta,
        document_id=str(doc_id),
        title=title,
        source_type=source_type,
        checksum=checksum,
        source_uri=source_uri,
        body=body,
    )
    return LoadedDocument(document=document, body=body)


def load_slack(text: str, *, checksum: str, source_uri: str) -> list[LoadedDocument]:
    """Normalize a Slack channel export: one Document per thread."""
    loaded: list[LoadedDocument] = []
    for meta, title, body in split_slack_threads(text):
        thread_id = _first_present(meta, ("thread_id",))
        if thread_id is None:
            continue  # registry reports files that yield zero documents
        document = _build_document(
            meta,
            document_id=str(thread_id),
            title=title or str(thread_id),
            source_type=SourceType.SLACK,
            checksum=checksum,
            source_uri=source_uri,
            body=body,
        )
        loaded.append(LoadedDocument(document=document, body=body))
    return loaded


def _build_document(
    meta: dict[str, Any],
    *,
    document_id: str,
    title: str,
    source_type: SourceType,
    checksum: str,
    source_uri: str,
    body: str,
) -> Document:
    """Map raw frontmatter onto the canonical Document schema (fail-closed)."""
    consumed = {
        *_ID_KEYS,
        "title",
        "document_type",
        "department",
        "classification",
        "allowed_roles",
        "allowed_departments",
        "owner_user_id",
        "owner",
        "document_version",
        "effective_date",
        "created_date",
        "status",
    }
    word_count = len(body.split())
    # Record which fail-closed defaults were applied so the registry can
    # report them as validation issues instead of guessing after the fact.
    defaults_applied = [
        field
        for field, missing in (
            ("classification", _clean_str(meta.get("classification")) is None),
            ("allowed_roles", not _normalize_str_list(meta.get("allowed_roles"))),
        )
        if missing
    ]
    # Coerce extras to JSON-safe values (YAML yields date objects) so the
    # metadata survives a registry JSONL round-trip unchanged.
    extra = _jsonify({k: v for k, v in meta.items() if k not in consumed})
    if defaults_applied:
        extra["_defaults_applied"] = defaults_applied
    return Document(
        document_id=document_id,
        title=title,
        source_type=source_type,
        document_type=_clean_str(meta.get("document_type")) or _DEFAULT_DOC_TYPE[source_type],
        department=_clean_str(meta.get("department")),
        classification=_parse_classification(meta.get("classification")),
        allowed_roles=_normalize_str_list(meta.get("allowed_roles")) or ("admin",),
        allowed_departments=_normalize_str_list(meta.get("allowed_departments")),
        owner_user_id=_clean_str(meta.get("owner_user_id")) or _clean_str(meta.get("owner")),
        document_version=_clean_str(meta.get("document_version")) or "v1",
        effective_date=_parse_date(meta.get("effective_date")),
        created_date=_parse_date(meta.get("created_date")),
        status=_parse_status(meta.get("status")),
        source_uri=source_uri,
        checksum=checksum,
        word_count=word_count,
        estimated_tokens=round(word_count * _TOKENS_PER_WORD),
        # Preserve every unmapped frontmatter field (tags, related_*, ...):
        # nothing from the corpus is silently discarded.
        metadata=extra,
    )


# --- small normalization helpers (tolerate the corpus's real-world messiness) ---


def _jsonify(value: Any) -> Any:
    """Recursively convert YAML-parsed values (dates, tuples) to JSON-safe ones."""
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonify(v) for v in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _first_present(meta: dict[str, Any], keys: tuple[str, ...]) -> Any | None:
    for key in keys:
        if meta.get(key) is not None:
            return meta[key]
    return None


def _first_match(pattern: re.Pattern[str], body: str) -> str | None:
    match = pattern.search(body)
    return match.group("title").strip() if match else None


def _clean_str(value: Any) -> str | None:
    """Coerce to a stripped string; treat empty / 'none' / 'null' as missing."""
    if value is None:
        return None
    text = str(value).strip()
    return text if text and text.lower() not in {"none", "null"} else None


def _normalize_str_list(value: Any) -> tuple[str, ...]:
    """Normalize a frontmatter list (or single string) to a clean tuple."""
    if value is None:
        return ()
    items = value if isinstance(value, list) else [value]
    cleaned = [c for item in items if (c := _clean_str(item)) is not None]
    return tuple(cleaned)


def _parse_classification(value: Any) -> Classification:
    """Fail-closed: unknown or missing classification becomes RESTRICTED."""
    text = _clean_str(value)
    try:
        return Classification(text) if text else Classification.RESTRICTED
    except ValueError:
        return Classification.RESTRICTED


def _parse_status(value: Any) -> DocumentStatus:
    text = _clean_str(value)
    try:
        return DocumentStatus(text) if text else DocumentStatus.ACTIVE
    except ValueError:
        return DocumentStatus.ACTIVE


def _parse_date(value: Any) -> date | None:
    """YAML may give us a date, a datetime, or a string; normalize to date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean_str(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None
