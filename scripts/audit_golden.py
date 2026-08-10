"""Audit the Phase 8 golden dataset.

Validates:
1. Both ``development.jsonl`` and ``holdout.jsonl`` exist and parse.
2. Every line has the required fields with non-empty values.
3. dev and holdout ids are disjoint.
4. Every CLAUDE.md §14 category is represented in BOTH splits.
5. Per-category counts are reasonable.

Exits 0 on success, 1 on any validation failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_CATEGORIES = {
    "direct_factual",
    "exact_identifier",
    "semantic_paraphrase",
    "procedural",
    "multi_document",
    "unanswerable",
    "authorization_restricted",
    "prompt_injection",
    "cache_safety",
}

REQUIRED_FIELDS = (
    "id",
    "query",
    "category",
    "expected_answer",
    "expected_chunk_sources",
    "expected_documents",
    "expected_roles",
    "expected_route",
    "expected_abstain",
    "min_top_k",
    "difficulty",
    "is_holdout",
    "source",
)


def _load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[audit] {path}:{ln} invalid JSON: {exc}", file=sys.stderr)
                raise
            out.append(rec)
    return out


def audit(golden_dir: Path) -> int:
    failures: list[str] = []

    dev_path = golden_dir / "development.jsonl"
    holdout_path = golden_dir / "holdout.jsonl"
    if not dev_path.exists():
        failures.append(f"missing {dev_path}")
    if not holdout_path.exists():
        failures.append(f"missing {holdout_path}")
    if failures:
        for f in failures:
            print(f"[audit] FAIL: {f}", file=sys.stderr)
        return 1

    dev = _load_jsonl(dev_path)
    holdout = _load_jsonl(holdout_path)
    print(f"[audit] dev={len(dev)}  holdout={len(holdout)}  total={len(dev) + len(holdout)}")

    # Required fields
    for split_name, items in [("dev", dev), ("holdout", holdout)]:
        for it in items:
            for field in REQUIRED_FIELDS:
                if field not in it:
                    failures.append(f"{split_name}/{it.get('id', '?')} missing field {field}")
                    break
            if it["category"] not in REQUIRED_CATEGORIES:
                failures.append(f"{it['id']} has unknown category {it['category']!r}")
            if not it["query"].strip():
                failures.append(f"{it['id']} has empty query")

    # Unique ids within and across splits
    all_ids = [it["id"] for it in dev] + [it["id"] for it in holdout]
    if len(set(all_ids)) != len(all_ids):
        failures.append("duplicate ids detected")
    dev_set = {it["id"] for it in dev}
    holdout_set = {it["id"] for it in holdout}
    overlap = dev_set & holdout_set
    if overlap:
        failures.append(f"dev/holdout overlap: {sorted(overlap)[:10]}")

    # Required categories present in BOTH splits
    for split_name, items in [("dev", dev), ("holdout", holdout)]:
        cats = {it["category"] for it in items}
        missing = REQUIRED_CATEGORIES - cats
        if missing:
            failures.append(f"{split_name} missing categories: {sorted(missing)}")

    # Per-category counts
    print("[audit] per-category counts:")
    for cat in sorted(REQUIRED_CATEGORIES):
        n_dev = sum(1 for it in dev if it["category"] == cat)
        n_holdout = sum(1 for it in holdout if it["category"] == cat)
        print(f"  {cat:<24} dev={n_dev:<4} holdout={n_holdout:<4}")

    if failures:
        print("\n[audit] FAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("\n[audit] OK — schema valid, splits disjoint, all categories present.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "golden_dir",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parent.parent / "data" / "golden",
    )
    args = parser.parse_args()
    return audit(args.golden_dir)


if __name__ == "__main__":
    raise SystemExit(main())
