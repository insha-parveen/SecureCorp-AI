"""Frontmatter and embedded-YAML parsing utilities.

This module is purely about *format*, not domain meaning:

- ``parse_frontmatter``: splits a ``---``-delimited YAML header from a
  Markdown body. Used by the generic loader for every standard corpus file
  (policies, knowledge base, emails, meetings, jira, github).
- ``split_slack_threads``: splits a Slack channel export into per-thread
  segments, each carrying its own ```yaml`` metadata block. Slack is the
  only corpus format with *multiple* independently-authorized documents
  inside a single file, so it gets its own splitter.

Keeping parsing here (with no knowledge of Document/Chunk models) lets the
loaders stay focused on normalization and keeps this code trivially testable.
"""

import re
from typing import Any

import yaml

# Matches a leading "---\n<yaml>\n---" frontmatter header.
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Matches a fenced ```yaml ... ``` metadata block (used inside Slack files).
_YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)

# A Slack file contains "## Thread N: <title>" sections; split before each.
_THREAD_SPLIT_RE = re.compile(r"^(?=## Thread )", re.MULTILINE)
_THREAD_HEADING_RE = re.compile(r"^## Thread \d+:\s*(?P<title>.+?)\s*$", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from a Markdown document.

    Returns ``(metadata, body)``. If no frontmatter is present (or it is not
    a YAML mapping), returns ``({}, text)`` so callers can decide how to
    handle metadata-less files instead of crashing mid-corpus-walk.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}, text
    if not isinstance(loaded, dict):
        return {}, text
    return loaded, text[match.end() :]


def split_slack_threads(text: str) -> list[tuple[dict[str, Any], str, str]]:
    """Split a Slack channel export into ``(metadata, title, thread_text)`` tuples.

    Each "## Thread N: <title>" section carries one fenced ```yaml`` block with
    its own ``thread_id``, ``classification``, and ``allowed_roles`` — so each
    thread becomes an independent Document downstream. Segments without a YAML
    block (e.g. the channel header before the first thread) are skipped.
    """
    threads: list[tuple[dict[str, Any], str, str]] = []
    for segment in _THREAD_SPLIT_RE.split(text):
        fence = _YAML_FENCE_RE.search(segment)
        if not fence:
            continue
        try:
            meta = yaml.safe_load(fence.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        heading = _THREAD_HEADING_RE.search(segment)
        title = heading.group("title") if heading else ""
        # Thread body = segment with the metadata fence removed.
        body = (segment[: fence.start()] + segment[fence.end() :]).strip()
        threads.append((meta, title, body))
    return threads
