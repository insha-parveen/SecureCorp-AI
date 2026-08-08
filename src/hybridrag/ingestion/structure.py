"""Markdown structure extraction: body text → ordered heading-scoped sections.

Policies, SOPs, knowledge-base articles, Jira issues, and GitHub artifacts in
the corpus are all heading-structured Markdown. Extracting that structure
before chunking is what lets the chunker keep a policy clause with its heading
and record a meaningful ``section_title`` for citations.

The parser tracks a heading *path* so a chunk taken from "### 3.1 Standard
Remote Work Limit" can report the full trail
("3. Remote Work Framework > 3.1 Standard Remote Work Limit") rather than an
ambiguous leaf title.
"""

import re

# ATX heading: 1-6 '#' followed by text. Setext headings do not appear in the
# corpus, so they are intentionally unsupported.
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")

# Fenced code blocks must not be scanned for headings — a '# comment' line
# inside a fence is code, not structure.
_FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Horizontal rules used as visual separators in the corpus (e.g. the long
# '------' divider in meeting transcripts).
_HRULE_RE = re.compile(r"^\s*([-*_]\s*){3,}$")


class Section:
    """A heading-delimited span of a document body."""

    def __init__(self, title: str | None, path: tuple[str, ...], level: int, text: str) -> None:
        self.title = title
        self.path = path
        self.level = level
        self.text = text

    @property
    def display_title(self) -> str | None:
        """The heading trail joined for use as ``Chunk.section_title``."""
        parts = [p for p in self.path if p]
        return " > ".join(parts) if parts else None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Section(path={self.path!r}, chars={len(self.text)})"


def parse_sections(body: str) -> list[Section]:
    """Split a Markdown body into heading-scoped sections in document order.

    Text appearing before the first heading becomes a leading section with a
    ``None`` title and empty path. Documents with no headings at all yield a
    single untitled section holding the whole body, so callers never need a
    special case.
    """
    sections: list[Section] = []
    path: list[str] = []
    current_title: str | None = None
    current_level = 0
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(Section(current_title, tuple(path), current_level, text))
        buffer.clear()

    for line in body.split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue
        heading = None if in_fence else _HEADING_RE.match(line)
        if heading is None:
            # Drop decorative horizontal rules; they carry no content and would
            # otherwise survive as noise inside chunk text.
            if not _HRULE_RE.match(line):
                buffer.append(line)
            continue
        flush()
        level = len(heading.group("hashes"))
        title = heading.group("title").strip()
        # Pop deeper/sibling headings so the path reflects true nesting.
        del path[level - 1 :]
        # Pad if the document skips a level (e.g. '#' straight to '###').
        while len(path) < level - 1:
            path.append("")
        path.append(title)
        current_title = title
        current_level = level

    flush()
    if not sections:
        text = body.strip()
        return [Section(None, (), 0, text)] if text else []
    return sections
