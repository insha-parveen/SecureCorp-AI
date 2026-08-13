"""Analytics endpoints for the dashboard surface.

These endpoints query the ``query_logs`` table to provide real-time
metrics on system usage, performance, and cache efficiency. Every value
is scoped to the caller's ``tenant_id`` (from the verified JWT), so one
tenant never sees another tenant's analytics.

If the database is unreachable, ``DatabaseManager.execute_read`` returns
an empty list (graceful degradation), and these endpoints return zeroed
shapes rather than raising.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from hybridrag.api.auth import current_user_from_cookie
from hybridrag.authorization.models import UserContext

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    request: Request,
    user: UserContext = Depends(current_user_from_cookie()),
) -> dict[str, Any]:
    """Return high-level KPI tiles (Total Queries, Avg Latency, Cache Hit Rate, Refusal Rate)."""
    db = request.app.state.assistant._db
    tenant_id = user.tenant_id

    # 1. Total Queries
    total_res = db.execute_read(
        "SELECT COUNT(*) as count FROM query_logs WHERE tenant_id = %s", (tenant_id,)
    )
    total_queries = total_res[0]["count"] if total_res else 0

    if total_queries == 0:
        return {
            "total_queries": 0,
            "avg_latency": 0,
            "cache_hit_rate": 0,
            "refusal_rate": 0,
        }

    # 2. Avg Latency (report seconds to match the UI tile)
    latency_res = db.execute_read(
        "SELECT AVG(latency_ms) as avg_latency FROM query_logs WHERE tenant_id = %s", (tenant_id,)
    )
    avg_latency_ms = float(latency_res[0]["avg_latency"] or 0)

    # 3. Cache Hit Rate (L1 or L2)
    hits_res = db.execute_read(
        "SELECT COUNT(*) as count FROM query_logs WHERE tenant_id = %s AND cache_hit != 'MISS'",
        (tenant_id,),
    )
    hits = hits_res[0]["count"] if hits_res else 0
    cache_hit_rate = (hits / total_queries) * 100

    # 4. Refusal Rate
    refused_res = db.execute_read(
        "SELECT COUNT(*) as count FROM query_logs WHERE tenant_id = %s AND route = 'REFUSE'",
        (tenant_id,),
    )
    refused = refused_res[0]["count"] if refused_res else 0
    refusal_rate = (refused / total_queries) * 100

    return {
        "total_queries": total_queries,
        "avg_latency": round(avg_latency_ms / 1000, 2),
        "cache_hit_rate": round(cache_hit_rate, 1),
        "refusal_rate": round(refusal_rate, 1),
    }


@router.get("/queries-over-time")
async def get_queries_over_time(
    request: Request,
    user: UserContext = Depends(current_user_from_cookie()),
) -> list[dict[str, Any]]:
    """Return query counts for the last 7 days.

    Returns: ``[{ "label": "Mon", "value": 142 }, ...]``.
    """
    db = request.app.state.assistant._db
    tenant_id = user.tenant_id

    query = """
        SELECT
            to_char(created_at, 'Dy') as label,
            COUNT(*) as value
        FROM query_logs
        WHERE tenant_id = %s AND created_at > NOW() - INTERVAL '7 days'
        GROUP BY created_at::date, to_char(created_at, 'Dy')
        ORDER BY created_at::date ASC
    """
    res = db.execute_read(query, (tenant_id,))
    # Normalize the count to a plain int (psycopg returns it as int already).
    return [{"label": row["label"].strip(), "value": int(row["value"])} for row in res]


@router.get("/query-types")
async def get_query_types(
    request: Request,
    user: UserContext = Depends(current_user_from_cookie()),
) -> list[dict[str, Any]]:
    """Return breakdown of queries by route.

    Returns: ``[{ "label": "Document RAG", "value": 68, "color": "..." }, ...]``.
    """
    db = request.app.state.assistant._db
    tenant_id = user.tenant_id

    query = "SELECT route, COUNT(*) as count FROM query_logs WHERE tenant_id = %s GROUP BY route"
    res = db.execute_read(query, (tenant_id,))

    # Map routes to human labels and chart-series colors.
    route_map = {
        "DOCUMENT_RAG": {"label": "Document RAG", "color": "var(--color-series-1)"},
        "STRUCTURED_SQL": {"label": "SQL / Structured", "color": "var(--color-series-3)"},
        "REFUSE": {"label": "Refused / Other", "color": "var(--color-series-6)"},
    }

    total = sum(int(row["count"]) for row in res)
    result: list[dict[str, Any]] = []
    for row in res:
        info = route_map.get(row["route"], {"label": "Other", "color": "var(--color-series-7)"})
        result.append(
            {
                "label": info["label"],
                "value": round((int(row["count"]) / total) * 100, 1) if total > 0 else 0,
                "color": info["color"],
            }
        )
    return result
