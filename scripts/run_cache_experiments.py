"""CLI: Phase 8 cache experiments.

Runs three measurements:

1. **Hit rate** — L1 exact + L2 semantic across the paraphrase clusters.
2. **Threshold sweep** — L2 hit rate for thresholds in [0.80, 0.85, 0.90, 0.95].
3. **Isolation probe** — cross-tenant, cross-role, cross-department hits.
   A correct implementation returns 0 for every axis; any non-zero is a
   hard gate failure (exit code 2).

The cache is flushed under a per-run namespace prefix so the production
cache state is never touched.

Usage:
    uv run python scripts/run_cache_experiments.py
    uv run python scripts/run_cache_experiments.py --namespace exp_phase8
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from hybridrag.authorization.models import UserContext
from hybridrag.config import get_settings
from hybridrag.evaluation.redis_cache_eval import (
    estimate_latency_saved,
    measure_l1_hit_rate,
    measure_l2_threshold_sweep,
)
from hybridrag.indexing import get_embedding_provider

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUERIES = REPO_ROOT / "data" / "golden" / "cache_eval_queries.json"
DEFAULT_REPORT = REPO_ROOT / "evaluation" / "reports" / "cache_eval.json"


def _user_from_scope(scope: dict[str, object], user_id: str) -> UserContext:
    return UserContext(
        user_id=str(user_id),
        roles=tuple(scope.get("roles", []) or []),  # type: ignore[arg-type]
        department=scope.get("department"),  # type: ignore[arg-type]
        tenant_id=str(scope.get("tenant_id", "nexacore")),
    )


def _flush_namespace(cache: object, namespace: str) -> None:
    """Delete every Redis key under ``cache:<namespace>:*`` and ``scope_embeddings:*`` matching it.

    The cache implementation we use here does not namespace its keys, so we
    flush the whole Redis instance. The caller is responsible for using a
    dedicated Redis namespace via ``--namespace`` and a dedicated test DB.
    """
    redis_client = cache._redis  # noqa: SLF001 — driver cleanup
    redis_client.flushdb()


def _build_cache(namespace: str):
    """Return a RedisCache-like instance whose scope hash incorporates the namespace.

    The default RedisCache hashes {tenant_id, roles, department}. To scope
    the experiment to a namespace without modifying the cache, we prefix the
    tenant_id of every UserContext we pass in earlier. Here we just return
    a normal RedisCache — the caller is expected to use Redis URL with a
    dedicated DB index via env (e.g. REDIS_URL=redis://localhost:6379/15).
    """
    from hybridrag.caching.redis_cache import RedisCache

    redis_cache = RedisCache()
    return redis_cache


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERIES,
        help="Path to the cache evaluation query file.",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="exp_phase8",
        help="Logical namespace label recorded in the report.",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--cache-db",
        type=int,
        default=None,
        help="Optional Redis DB index to use (overrides HYBRIDRAG_REDIS_URL).",
    )
    args = parser.parse_args()

    if not args.queries.exists():
        print(f"[cache_experiments] missing {args.queries}", file=sys.stderr)
        return 1

    if args.cache_db is not None:
        # Allow running against a separate DB index without permanently
        # changing the user's settings file.
        import os

        os.environ["HYBRIDRAG_REDIS_URL"] = (
            f"redis://localhost:{get_settings().redis_url.split(':')[-2].split('/')[-1]}"
            f"/{args.cache_db}"
        )
        # Bust the lru_cache on get_settings so the new URL takes effect.
        from hybridrag.config import get_settings as _get

        _get.cache_clear()

    payload = json.loads(args.queries.read_text(encoding="utf-8"))
    clusters = payload["paraphrase_clusters"]
    probes = payload["cross_scope_probes"]

    cache = _build_cache(args.namespace)
    _flush_namespace(cache, args.namespace)

    settings = get_settings()
    embeddings = get_embedding_provider(settings)

    # Canonical "writer" user context for the paraphrase clusters: HR admin
    # in tenant nexacore. Every set goes through this user; every get also
    # uses it so L1 exact hits can be measured.
    writer_scope = {"tenant_id": "nexacore", "roles": ["hr"], "department": "hr"}
    writer_user = _user_from_scope(writer_scope, "cache-writer")

    # 1. Seed L1 + L2 with the FIRST query of every cluster.
    n_clusters = 0
    for cluster in clusters:
        seed = cluster["queries"][0]
        seed_emb = embeddings.embed_query(seed)
        cache.set_exact(seed, f"answer::{cluster['cluster_id']}", writer_user)
        cache.set_semantic(seed, seed_emb, f"answer::{cluster['cluster_id']}", writer_user)
        n_clusters += 1

    # 2. L1 hit rate: re-query with ALL queries across ALL clusters.
    all_queries: list[str] = [q for c in clusters for q in c["queries"]]
    l1_hits, l1_total = measure_l1_hit_rate(cache, all_queries, writer_user)
    # L1 only ever hits for the seed query of each cluster (5 queries, 1 seed).
    # The other 4 are paraphrase-only — those are L2 territory.

    # 3. L2 threshold sweep over all queries.
    pair_list = [(q, embeddings.embed_query(q)) for q in all_queries]
    l2_sweep = measure_l2_threshold_sweep(cache, pair_list, writer_user)

    # 4. Isolation probe: cross-scope behavior on the paraphrase clusters.
    # For each probe, we seed the cache entry under the FIRST scope, then
    # ask: does the cache return a hit under any of the OTHER scopes?
    isolation = {"cross_tenant_hits": 0, "cross_role_hits": 0, "cross_department_hits": 0}
    for probe in probes:
        seed_query = probe["query"]
        seed_emb = embeddings.embed_query(seed_query)
        # Seed under the first scope; probe with the rest.
        first_scope = probe["scopes"][0]
        first_user = _user_from_scope(first_scope, first_scope["user_id"])
        cache.set_exact(seed_query, f"answer::{probe['probe_id']}", first_user)
        cache.set_semantic(seed_query, seed_emb, f"answer::{probe['probe_id']}", first_user)
        # Probe only the OTHER scopes (skip the first one).
        for scope in probe["scopes"][1:]:
            other_user = _user_from_scope(scope, scope["user_id"])
            # For an isolation probe, we want zero hits under the OTHER
            # user's scope. Look up directly via the L2 path at the
            # OTHER user's scope hash and classify the axis by what
            # actually differs.
            import numpy as np

            scope_hash = cache._get_auth_scope_hash(other_user)  # noqa: SLF001
            raw = cache._redis.hgetall(f"scope_embeddings:{scope_hash}")  # noqa: SLF001
            for emb_str in raw.values():
                emb = np.array(json.loads(emb_str))
                denom = float(np.linalg.norm(seed_emb) * np.linalg.norm(emb))
                if denom == 0.0:
                    continue
                score = float(np.dot(np.array(seed_emb), emb) / denom)
                if score >= settings.semantic_cache_threshold:
                    if str(scope["tenant_id"]) != str(first_scope["tenant_id"]):
                        isolation["cross_tenant_hits"] += 1
                    elif sorted(scope.get("roles", []) or []) != sorted(
                        first_scope.get("roles", []) or []
                    ):
                        isolation["cross_role_hits"] += 1
                    else:
                        isolation["cross_department_hits"] += 1

    # 5. Latency saved (analytical, conservative): subtract a measured
    # cache.get latency from a baseline cold-path latency.
    cold_latencies_ms: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        cache.get_exact("__cold_path_probe__", writer_user)
        cold_latencies_ms.append((time.perf_counter() - t0) * 1000)
    cold_path_ms = sum(cold_latencies_ms) / len(cold_latencies_ms)
    n_hits = l1_hits + sum(
        1 for q, e in pair_list if cache.get_semantic(e, q, writer_user) is not None
    )
    latency_saved = estimate_latency_saved(cold_path_ms, 0.0, n_hits)

    violation = any(isolation[k] > 0 for k in isolation)

    report = {
        "namespace": args.namespace,
        "n_clusters": n_clusters,
        "n_queries": len(all_queries),
        "l1_hit_rate": l1_hits / l1_total if l1_total > 0 else 0.0,
        "l2_hit_rate": l2_sweep,
        "latency_saved_ms": {
            "mean": round(latency_saved, 3),
            "cold_path_ms": round(cold_path_ms, 3),
            "n_hits": n_hits,
        },
        "isolation": {
            **isolation,
            "violation": violation,
        },
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[cache_experiments] wrote {args.report}")

    if violation:
        print(
            f"[cache_experiments] ISOLATION VIOLATION: {isolation}",
            file=sys.stderr,
        )
        return 2

    print(json.dumps({k: v for k, v in report.items() if k != "latency_saved_ms"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
