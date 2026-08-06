"""Unit tests for frontmatter / embedded-YAML parsing (format layer only)."""

from hybridrag.ingestion import parse_frontmatter, split_slack_threads

DOC_WITH_FRONTMATTER = """---
document_id: HR-003
title: Remote Work Policy
allowed_roles:
  - employee
  - admin
---

# Remote Work Policy

Body text here.
"""

SLACK_EXPORT = """# Slack Channel: #eng-backend

## Thread 1: Authentication Service Failure

```yaml
thread_id: SLK-ENG-BE-001
classification: department_internal
allowed_roles: [manager, it, admin]
```

---

**2026-03-14 09:22 — Sunita Rao**

The auth service is failing.

## Thread 2: Cache Sizing

```yaml
thread_id: SLK-ENG-BE-002
classification: public
allowed_roles: [employee, admin]
```

**2026-03-20 11:00 — Rahul Sharma**

Redis memory discussion.
"""


class TestParseFrontmatter:
    def test_parses_metadata_and_body(self) -> None:
        meta, body = parse_frontmatter(DOC_WITH_FRONTMATTER)
        assert meta["document_id"] == "HR-003"
        assert meta["allowed_roles"] == ["employee", "admin"]
        assert body.startswith("\n# Remote Work Policy") or body.startswith(
            "# Remote Work Policy"
        )

    def test_no_frontmatter_returns_empty_meta(self) -> None:
        meta, body = parse_frontmatter("# Just a heading\n\nText.")
        assert meta == {}
        assert body == "# Just a heading\n\nText."

    def test_malformed_yaml_returns_empty_meta(self) -> None:
        text = "---\n: [unclosed\n---\n\nBody."
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_non_mapping_yaml_returns_empty_meta(self) -> None:
        text = "---\n- just\n- a list\n---\nBody."
        meta, _ = parse_frontmatter(text)
        assert meta == {}


class TestSplitSlackThreads:
    def test_one_document_per_thread(self) -> None:
        threads = split_slack_threads(SLACK_EXPORT)
        assert len(threads) == 2
        meta1, title1, body1 = threads[0]
        assert meta1["thread_id"] == "SLK-ENG-BE-001"
        assert title1 == "Authentication Service Failure"
        assert "auth service is failing" in body1
        assert "```yaml" not in body1  # metadata fence stripped from body

    def test_threads_keep_independent_auth_metadata(self) -> None:
        threads = split_slack_threads(SLACK_EXPORT)
        assert threads[0][0]["classification"] == "department_internal"
        assert threads[1][0]["classification"] == "public"

    def test_text_without_threads_yields_nothing(self) -> None:
        assert split_slack_threads("# Channel header only\n\nNo threads.") == []
