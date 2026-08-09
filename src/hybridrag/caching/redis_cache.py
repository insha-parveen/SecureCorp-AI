"""Caching layer for SecureCorp AI.

This module implements an authorization-aware cache using Redis.
It supports both L1 (Exact) and L2 (Semantic) caching, ensuring that
cached answers never cross authorization boundaries.
"""

import hashlib
import json
import logging
from typing import Any

import redis

from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Authorization-aware cache implemented with Redis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        # decode_responses=True makes the client return str rather than bytes.
        # ``Any`` keeps call sites simple: every get/set path deals in str.
        self._redis: Any = redis.from_url(self._settings.redis_url, decode_responses=True)
        self._ttl = self._settings.cache_ttl

    def _get_auth_scope_hash(self, user_context: UserContext) -> str:
        """Create a stable hash of the user's security scope.

        Two users with the same roles, department, and tenant should have
        the same hash, as they are authorized to see the same data.
        """
        # Sort roles to ensure stable hashing
        scope_string = (
            f"{user_context.tenant_id}|"
            f"{','.join(sorted(user_context.roles))}|"
            f"{user_context.department}"
        )
        return hashlib.sha256(scope_string.encode()).hexdigest()

    def _build_cache_key(self, query: str, scope_hash: str, semantic: bool = False) -> str:
        """Build a namespaced cache key.
        Format: cache:{scope_hash}:{type}:{query_hash}
        """
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
        cache_type = "semantic" if semantic else "exact"
        return f"cache:{scope_hash}:{cache_type}:{query_hash}"

    def get_exact(self, query: str, user_context: UserContext) -> str | None:
        """Retrieve an exact match from the L1 cache."""
        scope_hash = self._get_auth_scope_hash(user_context)
        key = self._build_cache_key(query, scope_hash)

        result = self._redis.get(key)
        if result:
            logger.info(f"L1 Cache Hit for query: {query[:30]}...")
            return str(result)
        return None

    def set_exact(self, query: str, answer: str, user_context: UserContext) -> None:
        """Store an answer in the L1 cache."""
        scope_hash = self._get_auth_scope_hash(user_context)
        key = self._build_cache_key(query, scope_hash)
        self._redis.setex(key, self._ttl, answer)

    def get_semantic(
        self, query_embedding: list[float], query: str, user_context: UserContext
    ) -> str | None:
        """Retrieve a semantically similar match from the L2 cache.

        Note: In a full production system, this would use RedisVL or RedisSearch.
        For this implementation, we store embeddings in a scope-specific set and
        calculate similarity for candidates.
        """
        scope_hash = self._get_auth_scope_hash(user_context)

        # 1. Get all cached queries for this specific security scope
        # We store a mapping of {query_hash: embedding} in a Redis Hash for each scope
        scope_key = f"scope_embeddings:{scope_hash}"
        all_cached_embeddings = self._redis.hgetall(scope_key)

        if not all_cached_embeddings:
            return None

        import numpy as np

        q_vec = np.array(query_embedding)

        best_score = -1.0
        best_answer_key = None

        for q_hash, emb_str in all_cached_embeddings.items():
            emb = np.array(json.loads(emb_str))

            # Cosine Similarity
            score = np.dot(q_vec, emb) / (np.linalg.norm(q_vec) * np.linalg.norm(emb))

            if score > best_score:
                best_score = score
                best_answer_key = f"cache:{scope_hash}:semantic:{q_hash}"

        if best_score >= self._settings.semantic_cache_threshold:
            logger.info(f"L2 Cache Hit (score: {best_score:.3f}) for query: {query[:30]}...")
            return self._redis.get(best_answer_key) if best_answer_key else None

        return None

    def set_semantic(
        self, query: str, query_embedding: list[float], answer: str, user_context: UserContext
    ) -> None:
        """Store an answer and its embedding in the L2 cache."""
        scope_hash = self._get_auth_scope_hash(user_context)
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()

        # Store the answer
        key = self._build_cache_key(query, scope_hash, semantic=True)
        self._redis.setex(key, self._ttl, answer)

        # Store the embedding for future similarity searches
        scope_key = f"scope_embeddings:{scope_hash}"
        self._redis.hset(scope_key, query_hash, json.dumps(query_embedding))
        # Set TTL on the scope index as well
        self._redis.expire(scope_key, self._ttl)
