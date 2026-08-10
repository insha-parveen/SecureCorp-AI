"""Unit tests for the Phase 8 cache experiment helpers.

These exercise the threshold/isolation helpers against an in-memory fake of
the Redis cache — no Redis required, no real network. The end-to-end
``run_cache_experiments.py`` CLI is exercised separately via subprocess when
``PHASE8_RUN=1`` is set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hybridrag.authorization.models import UserContext
from hybridrag.evaluation.redis_cache_eval import (
    estimate_latency_saved,
    measure_l1_hit_rate,
    measure_l2_threshold_sweep,
)


@dataclass
class _FakeRedis:
    """In-memory stand-in for redis.Redis — supports get/set/hgetall/hset/flushdb."""

    store: dict[str, str] = field(default_factory=dict)
    hashes: dict[str, dict[str, str]] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        del ttl  # ttl not exercised in unit tests
        self.store[key] = value

    def hset(self, key: str, field_: str, value: str) -> None:
        self.hashes.setdefault(key, {})[field_] = value

    def hgetall(self, key: str) -> dict[str, str]:
        return dict(self.hashes.get(key, {}))

    def flushdb(self) -> None:
        self.store.clear()
        self.hashes.clear()


@dataclass
class _FakeCache:
    """In-memory stand-in for RedisCache — only the surface the helpers touch."""

    redis: _FakeRedis = field(default_factory=_FakeRedis)
    threshold: float = 0.95
    # Expose the private API the helpers use intentionally.
    _settings: Any = None
    _redis: _FakeRedis = field(init=False)

    def __post_init__(self) -> None:
        self._redis = self.redis
        self._settings = type("S", (), {"semantic_cache_threshold": self.threshold})()

    def _get_auth_scope_hash(self, user: UserContext) -> str:
        import hashlib

        s = f"{user.tenant_id}|{','.join(sorted(user.roles))}|{user.department}"
        return hashlib.sha256(s.encode()).hexdigest()


def test_measure_l1_hit_rate_reports_seeded_hits_only() -> None:
    cache = _FakeCache()
    user = UserContext(user_id="u", roles=("hr",), department="hr", tenant_id="nexacore")
    # Seed two distinct queries
    cache.redis.setex("k1", 60, "answer-1")
    cache.redis.setex("k2", 60, "answer-2")
    # The hash-based key the helper looks up is opaque; we just count
    # how many queries find something by writing through the cache
    # API directly. For unit-test purposes we stub get_exact too.
    fake_get = {"a": "answer-a", "b": None, "c": "answer-c"}
    cache.get_exact = lambda q, _u: fake_get.get(q)  # type: ignore[method-assign]

    hits, total = measure_l1_hit_rate(cache, ["a", "b", "c", "d"], user)
    assert hits == 2
    assert total == 4


def test_measure_l2_threshold_sweep_counts_per_threshold() -> None:
    cache = _FakeCache()
    user = UserContext(user_id="u", roles=("hr",), department="hr", tenant_id="nexacore")
    # Embeddings chosen so the cosine similarity is exactly 1.0.
    pair_list = [("q1", [1.0, 0.0, 0.0])]
    # Seed scope_embeddings so there is something to find.
    import json

    scope_hash = cache._get_auth_scope_hash(user)
    cache.redis.hset(f"scope_embeddings:{scope_hash}", "q1", json.dumps([1.0, 0.0, 0.0]))

    rates = measure_l2_threshold_sweep(cache, pair_list, user, thresholds=(0.80, 0.85, 0.90, 0.95))
    assert rates == {"0.80": 1.0, "0.85": 1.0, "0.90": 1.0, "0.95": 1.0}


def test_measure_l2_threshold_sweep_empty_pairs_returns_zeros() -> None:
    cache = _FakeCache()
    user = UserContext(user_id="u", roles=("hr",), department="hr", tenant_id="nexacore")
    rates = measure_l2_threshold_sweep(cache, [], user)
    assert rates == {"0.80": 0.0, "0.85": 0.0, "0.90": 0.0, "0.95": 0.0}


def test_estimate_latency_saved_clamps_at_zero() -> None:
    # Cold path faster than cache get → saved is 0.
    assert estimate_latency_saved(5.0, 20.0, 1) == 0.0
    # Cold path 100ms, cache 5ms → 95ms saved.
    assert estimate_latency_saved(100.0, 5.0, 10) == 95.0


def test_estimate_latency_saved_returns_per_hit_value() -> None:
    # The function returns per-hit saved, not total.
    assert estimate_latency_saved(120.0, 10.0, 1) == 110.0
