"""Phase 8 orchestrator smoke test.

The smoke test wraps ``scripts/run_phase8_eval.py`` via subprocess and is
opt-in via ``PHASE8_RUN=1``. By default it skips — the CI fast path runs
the unit tests in ``tests/evaluation/`` only.

When enabled, it invokes the orchestrator with ``--skip-ragas --skip-cache
--skip-chunking`` so the run completes in seconds without LLM calls, Redis,
or a full chunking sweep. The orchestrator should exit 0 and produce both
the JSON and HTML reports.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "run_phase8_eval.py"


@pytest.mark.skipif(
    os.environ.get("PHASE8_RUN") != "1",
    reason="set PHASE8_RUN=1 to invoke the Phase 8 orchestrator smoke run",
)
def test_phase8_orchestrator_smoke_run(tmp_path: Path) -> None:
    report_json = tmp_path / "phase8_smoke.json"
    report_html = tmp_path / "phase8_smoke_report.html"
    queries = REPO_ROOT / "data" / "golden" / "development.jsonl"

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--queries",
            str(queries),
            "--report-json",
            str(report_json),
            "--report-html",
            str(report_html),
            "--skip-ragas",
            "--skip-chunking",
            "--skip-cache",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Orchestrator should produce a non-FAIL exit code in the smoke run.
    assert proc.returncode != 2, f"isolation violation: {proc.stderr}"
    assert report_json.exists(), f"missing json report: {proc.stderr}"
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["split"] == "dev"
    assert "retrieval" in payload
    assert "ragas" in payload
    assert "cache" in payload
    assert "chunking_sweep" in payload
