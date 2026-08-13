"""Helpers for the Phase 8 cache experiments.

These wrap RedisCache with the three measurements the cache experiments need:

1. **Hit rate** — L1 (exact) and L2 (semantic) hit rates.
2. **Threshold sweep** — L2 hit rate for thresholds in [0.80, 0.85, 0.90, 0.95].
3. **Isolation probe** — cross-tenant, cross-role, cross-department hit counts.

The cache is left to flush under a per-run namespace prefix so prod cache
state is never touched (and so the same Redis instance can run multiple
experiments in parallel).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.caching.redis_cache import RedisCache

# Thresholds for the experiment's L2 sweep. Tuned against the corpus in
# Phase 8 §6; values outside this range are not validated.
DEFAULT_THRESHOLDS: tuple[float, ...] = (0.80, 0.85, 0.90, 0.95)


@dataclass(frozen=True)
class CacheHitResult:
    """Per-query hit classification the experiments need."""

    hit_l1: bool
    hit_l2: bool
    best_l2_score: float  # best cosine similarity; -1.0 if no cached entry
    threshold: float  # the threshold _used_ for the L2 decision


def _scope_to_user_context(scope: dict[str, Any]) -> UserContext:
    """Convert a JSON scope dict into a UserContext.

    Accepts ``roles`` as a list (JSON convention) and converts to tuple.
    """
    return UserContext(
        user_id=scope["user_id"],
        roles=tuple(scope.get("roles", [])),
        department=scope.get("department"),
        tenant_id=scope.get("tenant_id", "nexacore"),
    )


def _scope_key_variants(
    base: UserContext,
) -> dict[str, UserContext]:
    """Return user contexts that should each have a distinct cache scope.

    One scope per axis: tenant, role, department. Used by the isolation probe
    to assert that hitting the cache for the base scope returns NONE for any
    of the cross-axis scopes.
    """
    return {
        "cross_tenant": UserContext(
            user_id=base.user_id,
            roles=base.roles,
            department=base.department,
            tenant_id="alt_tenant",
        ),
        "cross_role": UserContext(
            user_id=base.user_id,
            roles=("admin",) if "admin" not in base.roles else ("employee",),
            department=base.department,
            tenant_id=base.tenant_id,
        ),
        "cross_department": UserContext(
            user_id=base.user_id,
            roles=base.roles,
            department="alt_dept",
            tenant_id=base.tenant_id,
        ),
    }


def _measure_l2_for_threshold(
    cache: RedisCache,
    query: str,
    query_embedding: list[float],
    user: UserContext,
    threshold: float,
) -> bool:
    """Run L2 lookup at a specific threshold, ignoring the cache's own setting.

    Returns True iff there is an entry whose cosine similarity >= threshold.
    Used by the threshold sweep — we evaluate directly rather than mutate the
    Settings because mutation would invalidate already-set semantic_cache_threshold.
    """
    scope_hash = cache._get_auth_scope_hash(user)  # noqa: SLF001 — intentional
    scope_key = f"scope_embeddings:{scope_hash}"
    raw = cache._redis.hgetall(scope_key)  # noqa: SLF001
    if not raw:
        return False
    import numpy as np

    q_vec = np.array(query_embedding)
    for emb_str in raw.values():
        emb = np.array(json.loads(emb_str))
        denom = float(np.linalg.norm(q_vec) * np.linalg.norm(emb))
        if denom == 0.0:
            continue
        score = float(np.dot(q_vec, emb) / denom)
        if score >= threshold:
            return True
    return False


def measure_l1_hit_rate(
    cache: RedisCache,
    queries: Iterable[str],
    user: UserContext,
) -> tuple[int, int]:
    """Return (hits, total) for L1 exact lookups."""
    n_total = 0
    n_hit = 0
    for q in queries:
        n_total += 1
        if cache.get_exact(q, user) is not None:
            n_hit += 1
    return n_hit, n_total


def measure_l2_threshold_sweep(
    cache: RedisCache,
    pairs: Iterable[tuple[str, list[float]]],
    user: UserContext,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
) -> dict[str, float]:
    """Return hit rate per threshold for the supplied (query, embedding) pairs."""
    materialized = list(pairs)
    n_total = len(materialized)
    hits: dict[str, int] = {f"{t:.2f}": 0 for t in thresholds}
    for q, emb in materialized:
        for t in thresholds:
            if _measure_l2_for_threshold(cache, q, emb, user, t):
                hits[f"{t:.2f}"] += 1
    return {k: (v / n_total if n_total > 0 else 0.0) for k, v in hits.items()}


def measure_isolation(
    cache: RedisCache,
    query: str,
    query_embedding: list[float],
    base: UserContext,
    ignore_l1: bool = True,
) -> dict[str, int]:
    """Probe cross-scope behavior: returns the number of L2 hits per axis.

    Each axis (tenant, role, department) checks whether the same query
    under a different scope reaches the cache entry for the base scope.
    A correct implementation returns 0 for every axis.
    """
    variants = _scope_key_variants(base)
    n_tenant = n_role = n_dept = 0
    for axis, other in variants.items():
        # L2 hit at the base scope's threshold
        hit = _measure_l2_for_threshold(
            cache,
            query,
            query_embedding,
            other,
            cache._settings.semantic_cache_threshold,  # noqa: SLF001
        )
        if hit:
            if axis == "cross_tenant":
                n_tenant += 1
            elif axis == "cross_role":
                n_role += 1
            elif axis == "cross_department":
                n_dept += 1
    return {
        "cross_tenant_hits": n_tenant,
        "cross_role_hits": n_role,
        "cross_department_hits": n_dept,
    }


def estimate_latency_saved(
    cold_path_ms: float,
    cache_get_ms: float,
    n_hits: int,
) -> float:
    """Mean latency saved per hit (analytical: cold_path - cache_get)."""
    per_hit = max(0.0, cold_path_ms - cache_get_ms)
    return per_hit
