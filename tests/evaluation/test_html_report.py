"""Unit tests for the Phase 8 HTML renderer.

The renderer is a pure JSON→HTML transformer; we never invoke the orchestrator
or any LLM/embedding code. Tests cover the schema of every section.
"""

from __future__ import annotations

import json
from pathlib import Path

from hybridrag.evaluation.html_report import write_report


def test_renderer_writes_html_with_each_section_header(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"
    payload = {
        "split": "dev",
        "timestamp": "2026-08-10T00:00:00Z",
        "pass_fail": "PASS",
        "retrieval": {
            "arms": [
                {
                    "strategy": "Hybrid-Rerank",
                    "overall": {
                        "recall_at_k": 0.92,
                        "mrr": 0.84,
                        "ndcg_at_k": 0.78,
                        "precision_at_k": 0.45,
                        "hit_at_1": 0.66,
                        "hits": 230,
                        "total": 250,
                    },
                    "by_category": {},
                }
            ]
        },
        "ragas": {
            "faithfulness": 0.91,
            "answer_relevancy": 0.87,
            "context_precision": 0.82,
            "context_recall": 0.79,
            "abstention_recall": 0.65,
        },
        "citations": {
            "valid_citation_rate": 0.98,
            "invalid_citation_rate": 0.02,
            "citation_coverage": 0.94,
            "n_items": 250,
            "n_abstentions": 12,
            "n_with_citations": 230,
        },
        "chunking_sweep": {
            "cells": [
                {
                    "cell_id": "baseline",
                    "params": {"target": 440, "max": 440, "overlap": 60, "min": 300},
                    "chunks_produced": 450,
                    "arms": {
                        "Hybrid-Rerank": {"recall_at_5": 0.92},
                        "BM25-Only": {"recall_at_5": 0.81},
                    },
                }
            ]
        },
        "cache": {
            "l1_hit_rate": 0.20,
            "l2_hit_rate": {"0.80": 0.85, "0.95": 0.30},
            "isolation": {
                "cross_tenant_hits": 0,
                "cross_role_hits": 0,
                "cross_department_hits": 0,
                "violation": False,
            },
        },
        "security": {
            "unauthorized_retrieval_count": 0,
            "security_leakage_rate": 0.0,
        },
    }
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    write_report(json_path, html_path)
    html = html_path.read_text(encoding="utf-8")

    # Every section header should appear.
    for header in (
        "Retrieval",
        "RAGAS",
        "Citations",
        "Chunking Sweep",
        "Cache",
        "Security",
    ):
        assert header in html

    # PASS banner should appear.
    assert "PASS" in html
    # Numbers should appear formatted (4-decimal Recall@5).
    assert "0.9200" in html


def test_renderer_handles_missing_sections(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"
    payload = {
        "split": "dev",
        "timestamp": "2026-08-10T00:00:00Z",
        "pass_fail": "PASS",
        "retrieval": {},
        "ragas": {"error": "ragas not installed"},
        "citations": {},
        "chunking_sweep": {},
        "cache": {},
        "security": {},
    }
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    write_report(json_path, html_path)
    html = html_path.read_text(encoding="utf-8")
    # Section headers should still appear even when empty.
    assert "Retrieval" in html
    assert "RAGAS" in html
    assert "ragas not installed" in html


def test_renderer_reflects_cache_isolation_violation(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"
    payload = {
        "split": "dev",
        "timestamp": "2026-08-10T00:00:00Z",
        "pass_fail": "FAIL",
        "retrieval": {},
        "ragas": {},
        "citations": {},
        "chunking_sweep": {},
        "cache": {
            "isolation": {
                "cross_tenant_hits": 1,
                "cross_role_hits": 0,
                "cross_department_hits": 0,
                "violation": True,
            }
        },
        "security": {},
    }
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    write_report(json_path, html_path)
    html = html_path.read_text(encoding="utf-8")
    assert "VIOLATION" in html
    assert "FAIL" in html
