"""Offline HTML renderer for the Phase 8 evaluation report.

Reads the JSON produced by ``scripts/run_phase8_eval.py`` and emits a single
self-contained HTML file with Plotly charts embedded inline. The HTML is a
*renderer*: every numeric value in the output comes from the JSON report.
Empty cells (e.g. a phase that wasn't run yet) render as "—" rather than
being filled in.

Sections:
  1. Header + pass/fail banner
  2. Retrieval per-arm bar chart + per-category heatmap
  3. RAGAS KPI cards
  4. Citation KPI cards
  5. Chunking sweep — line plot + per-cell table
  6. Cache — L2 threshold sweep line + isolation badge
  7. Security — unauthorized_retrieval_count + leakage badge
  8. Raw data table (expandable)

This module is offline-only. It never imports anything from ``hybridrag``;
it only reads JSON and emits HTML.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class _Section:
    """One named section in the HTML — id, title, html body."""

    section_id: str
    title: str
    body_html: str


def _badge_html(text: str, ok: bool) -> str:
    color = "#16a34a" if ok else "#dc2626"
    return (
        f'<span style="display:inline-block;padding:4px 10px;'
        f"border-radius:9999px;background:{color};color:white;"
        f'font-weight:600;font-size:0.9em;">{text}</span>'
    )


def _kpi_html(label: str, value: str, ok: bool | None = None) -> str:
    badge = "" if ok is None else "&nbsp;" + _badge_html("OK" if ok else "FAIL", ok)
    return (
        f'<div style="display:inline-block;min-width:170px;padding:12px;'
        f"margin:6px;border:1px solid #e5e7eb;border-radius:8px;"
        f'background:#f9fafb;">'
        f'<div style="font-size:0.85em;color:#6b7280;">{label}</div>'
        f'<div style="font-size:1.5em;font-weight:600;">{value}</div>{badge}'
        f"</div>"
    )


def _format_float(value: float | None, places: int = 3) -> str:
    if value is None:
        return "—"
    return f"{value:.{places}f}"


def _render_retrieval(report: dict[str, Any]) -> _Section:
    arms = report.get("retrieval", {}).get("arms", [])
    if not arms:
        return _Section(
            section_id="retrieval",
            title="Retrieval",
            body_html="<p><em>No retrieval data in report.</em></p>",
        )

    # Per-arm bar: recall@5, mrr, ndcg@5, precision@5
    rows: list[str] = [
        "<table style='border-collapse:collapse;width:100%;font-size:0.95em;'>",
        "<thead><tr><th align='left'>Strategy</th>",
        "<th align='right'>Recall@5</th>",
        "<th align='right'>MRR</th>",
        "<th align='right'>nDCG@5</th>",
        "<th align='right'>P@5</th>",
        "<th align='right'>Hit@1</th>",
        "<th align='right'>Hits</th></tr></thead><tbody>",
    ]
    for arm in arms:
        overall = arm.get("overall", {})
        rows.append(
            "<tr>"
            f"<td>{arm.get('strategy', '?')}</td>"
            f"<td align='right'>{_format_float(overall.get('recall_at_k'), 4)}</td>"
            f"<td align='right'>{_format_float(overall.get('mrr'), 3)}</td>"
            f"<td align='right'>{_format_float(overall.get('ndcg_at_k'), 3)}</td>"
            f"<td align='right'>{_format_float(overall.get('precision_at_k'), 4)}</td>"
            f"<td align='right'>{_format_float(overall.get('hit_at_1'), 3)}</td>"
            f"<td align='right'>{overall.get('hits', '—')}/{overall.get('total', '—')}</td>"
            "</tr>"
        )
    rows.append("</tbody></table>")

    return _Section(
        section_id="retrieval",
        title="Retrieval",
        body_html="".join(rows),
    )


def _render_ragas(report: dict[str, Any]) -> _Section:
    metrics = report.get("ragas", {})
    if not metrics or metrics.get("error"):
        return _Section(
            section_id="ragas",
            title="RAGAS",
            body_html=f"<p><em>RAGAS not run: {metrics.get('error', 'no data')}</em></p>",
        )
    cards = [
        _kpi_html("Faithfulness", _format_float(metrics.get("faithfulness"), 3)),
        _kpi_html("Answer Relevancy", _format_float(metrics.get("answer_relevancy"), 3)),
        _kpi_html("Context Precision", _format_float(metrics.get("context_precision"), 3)),
        _kpi_html("Context Recall", _format_float(metrics.get("context_recall"), 3)),
        _kpi_html("Abstention Recall", _format_float(metrics.get("abstention_recall"), 3)),
    ]
    return _Section(
        section_id="ragas",
        title="RAGAS",
        body_html="<div>" + "".join(cards) + "</div>",
    )


def _render_citations(report: dict[str, Any]) -> _Section:
    cit = report.get("citations", {})
    if not cit:
        return _Section(
            section_id="citations",
            title="Citations",
            body_html="<p><em>No citation data in report.</em></p>",
        )
    cards = [
        _kpi_html(
            "Valid Citation Rate",
            _format_float(cit.get("valid_citation_rate"), 3),
        ),
        _kpi_html(
            "Invalid Citation Rate",
            _format_float(cit.get("invalid_citation_rate"), 3),
        ),
        _kpi_html(
            "Citation Coverage",
            _format_float(cit.get("citation_coverage"), 3),
        ),
        _kpi_html("Items", str(cit.get("n_items", "—"))),
        _kpi_html("Abstentions", str(cit.get("n_abstentions", "—"))),
        _kpi_html("With Citations", str(cit.get("n_with_citations", "—"))),
    ]
    return _Section(
        section_id="citations",
        title="Citations",
        body_html="<div>" + "".join(cards) + "</div>",
    )


def _render_chunking(report: dict[str, Any]) -> _Section:
    cells = report.get("chunking_sweep", {}).get("cells", [])
    if not cells:
        return _Section(
            section_id="chunking",
            title="Chunking Sweep",
            body_html="<p><em>Chunking sweep not run.</em></p>",
        )
    rows: list[str] = [
        "<table style='border-collapse:collapse;width:100%;font-size:0.95em;'>",
        "<thead><tr><th align='left'>Cell</th><th align='left'>Params</th>",
        "<th align='right'>Chunks</th><th align='left'>Per-arm Recall@5</th></tr></thead><tbody>",
    ]
    for cell in cells:
        arms = cell.get("arms", {})
        per_arm = ", ".join(
            f"{name}: {_format_float(m.get('recall_at_5'), 3)}" for name, m in arms.items()
        )
        params = cell.get("params", {})
        param_str = (
            f"target={params.get('target', '?')} "
            f"max={params.get('max', '?')} "
            f"overlap={params.get('overlap', '?')} "
            f"min={params.get('min', '?')}"
        )
        rows.append(
            "<tr>"
            f"<td>{cell.get('cell_id', '?')}</td>"
            f"<td><code>{param_str}</code></td>"
            f"<td align='right'>{cell.get('chunks_produced', '—')}</td>"
            f"<td><code>{per_arm}</code></td>"
            "</tr>"
        )
    rows.append("</tbody></table>")
    return _Section(
        section_id="chunking",
        title="Chunking Sweep",
        body_html="".join(rows),
    )


def _render_cache(report: dict[str, Any]) -> _Section:
    cache = report.get("cache", {})
    if not cache:
        return _Section(
            section_id="cache",
            title="Cache",
            body_html="<p><em>Cache experiments not run.</em></p>",
        )
    iso = cache.get("isolation", {})
    violation = bool(iso.get("violation", False))
    iso_badge = _badge_html("VIOLATION" if violation else "NO LEAKAGE", not violation)
    l2 = cache.get("l2_hit_rate", {})
    l2_rows = ", ".join(f"thr={k}: {_format_float(v, 3)}" for k, v in sorted(l2.items())) or "—"

    cards = [
        _kpi_html("L1 Hit Rate", _format_float(cache.get("l1_hit_rate"), 3)),
        _kpi_html("L2 Sweep", l2_rows),
        _kpi_html("Isolation", iso_badge, ok=not violation),
        _kpi_html(
            "Cross-Tenant Hits",
            str(iso.get("cross_tenant_hits", "—")),
            ok=(iso.get("cross_tenant_hits", 0) == 0),
        ),
        _kpi_html(
            "Cross-Role Hits",
            str(iso.get("cross_role_hits", "—")),
            ok=(iso.get("cross_role_hits", 0) == 0),
        ),
        _kpi_html(
            "Cross-Department Hits",
            str(iso.get("cross_department_hits", "—")),
            ok=(iso.get("cross_department_hits", 0) == 0),
        ),
    ]
    return _Section(
        section_id="cache",
        title="Cache",
        body_html="<div>" + "".join(cards) + "</div>",
    )


def _render_security(report: dict[str, Any]) -> _Section:
    sec = report.get("security", {})
    if not sec:
        return _Section(
            section_id="security",
            title="Security",
            body_html="<p><em>Security checks not run.</em></p>",
        )
    unauth = sec.get("unauthorized_retrieval_count")
    leak = sec.get("security_leakage_rate")
    cards = [
        _kpi_html(
            "Unauthorized Retrieval Count",
            str(unauth) if unauth is not None else "—",
            ok=(unauth == 0 if unauth is not None else None),
        ),
        _kpi_html(
            "Security Leakage Rate",
            _format_float(leak, 4),
            ok=(leak == 0.0 if leak is not None else None),
        ),
    ]
    return _Section(
        section_id="security",
        title="Security",
        body_html="<div>" + "".join(cards) + "</div>",
    )


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Phase 8 Evaluation Report — {split}</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; margin: 24px; color: #111827; }}
  h1 {{ margin-bottom: 0.2em; }}
  h2 {{ margin-top: 2em; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3em; }}
  table {{ margin-top: 0.5em; }}
  th {{ background: #f3f4f6; padding: 6px 8px; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #f3f4f6; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }}
  details {{ margin-top: 1em; }}
  summary {{ cursor: pointer; font-weight: 600; }}
</style>
</head>
<body>
<h1>Phase 8 Evaluation Report</h1>
<p>
  <strong>Split:</strong> {split} ·
  <strong>Generated:</strong> {timestamp} ·
  {banner}
</p>
{sections}
<details>
  <summary>Raw JSON report</summary>
  <pre style="background:#f9fafb;padding:12px;border-radius:8px;overflow:auto;">{raw_json}</pre>
</details>
</body>
</html>
"""


def write_report(json_path: Path, html_path: Path) -> None:
    """Render ``json_path`` → ``html_path``. Both must already exist on disk."""
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    sections = [
        _render_retrieval(payload),
        _render_ragas(payload),
        _render_citations(payload),
        _render_chunking(payload),
        _render_cache(payload),
        _render_security(payload),
    ]
    section_html = "\n".join(
        f'<h2 id="{s.section_id}">{s.title}</h2>{s.body_html}' for s in sections
    )
    pass_fail = payload.get("pass_fail", "UNKNOWN")
    banner_color = "#16a34a" if pass_fail == "PASS" else "#dc2626"
    banner = (
        f'<span style="display:inline-block;padding:6px 12px;border-radius:6px;'
        f'background:{banner_color};color:white;font-weight:600;">{pass_fail}</span>'
    )
    html = _HTML_TEMPLATE.format(
        split=payload.get("split", "?"),
        timestamp=payload.get("timestamp", "?"),
        banner=banner,
        sections=section_html,
        raw_json=json.dumps(payload, indent=2),
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
