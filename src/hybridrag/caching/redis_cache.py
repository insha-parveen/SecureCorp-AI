"""Caching layer for SecureCorp AI.

This module implements an authorization-aware cache using Redis.
It supports both L1 (Exact) and L2 (Semantic) caching, ensuring that
cached answers never cross authorization boundaries.

Improvements over the original implementation:

  * **Version-stamped keys.** Every cache key embeds ``corpus_version``,
    ``embedding_model``, and ``cache_prompt_version``. Bumping any of
    those invalidates the affected cache cohort without a manual flush.
  * **Graceful degradation.** If Redis is unreachable, ``get_*`` returns
    ``None`` (cache miss) and ``set_*`` logs and skips the write, instead
    of raising and breaking the request path.
  * **Bounded semantic scan.** The L2 scan is capped at
    ``Settings.semantic_cache_max_scan`` entries per scope to keep the
    O(n) cosine comparison bounded.
  * **Correct auth scope.** The scope hash includes roles, department,
    and tenant — but *not* user_id, so two users with identical access
    can share cache entries (correct reuse).
"""

import hashlib
import json
import logging
from typing import Any

import redis

from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings
from hybridrag.domain.models import FinalResponse

logger = logging.getLogger(__name__)


class RedisCache:
    """Authorization-aware cache implemented with Redis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._redis: Any = None
        self._ttl = self._settings.cache_ttl
        if self._settings.cache_enabled:
            try:
                # decode_responses=True makes the client return str rather than
                # bytes. ``Any`` keeps call sites simple: every get/set path
                # deals in str.
                self._redis = redis.from_url(
                    self._settings.redis_url, decode_responses=True, socket_timeout=1
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Redis unavailable at startup; caching disabled: %s", exc)
                self._redis = None

    # -- public API --------------------------------------------------------

    def get_exact(self, query: str, user_context: UserContext) -> FinalResponse | None:
        """Retrieve an exact match from the L1 cache.

        Returns ``None`` on any Redis error (graceful cache miss).
        """
        if self._redis is None:
            return None
        try:
            scope_hash = self._get_auth_scope_hash(user_context)
            key = self._build_cache_key(query, scope_hash)

            result = self._redis.get(key)
            if result:
                logger.info("L1 Cache Hit for query: %s...", query[:30])
                return FinalResponse.model_validate_json(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("L1 cache read failed (treating as miss): %s", exc)
        return None

    def set_exact(self, query: str, response: FinalResponse, user_context: UserContext) -> None:
        """Store an answer in the L1 cache."""
        if self._redis is None or not response:
            return
        try:
            scope_hash = self._get_auth_scope_hash(user_context)
            key = self._build_cache_key(query, scope_hash)
            self._redis.setex(key, self._ttl, response.model_dump_json())
        except Exception as exc:  # noqa: BLE001
            logger.warning("L1 cache write failed (skipping): %s", exc)

    def get_semantic(
        self, query_embedding: list[float], query: str, user_context: UserContext
    ) -> FinalResponse | None:
        """Retrieve a semantically similar match from the L2 cache.

        Returns ``None`` on any Redis error (graceful cache miss).

        Uses vector similarity over stored embeddings in the user's scope.
        The scan is capped at ``Settings.semantic_cache_max_scan`` entries.
        """
        if self._redis is None:
            return None
        try:
            scope_hash = self._get_auth_scope_hash(user_context)

            # 1. Get all cached queries for this specific security scope.
            # Store a mapping of {query_hash: embedding} in a Redis Hash.
            scope_key = f"scope_embeddings:{scope_hash}"
            all_cached_embeddings = self._redis.hgetall(scope_key)

            if not all_cached_embeddings:
                return None

            import numpy as np

            q_vec = np.array(query_embedding, dtype=float)

            best_score = -1.0
            best_answer_key: str | None = None

            # 2. Bounded scan: cap the number of candidate embeddings we
            # compare to prevent unbounded O(n) work on active scopes.
            entries = list(all_cached_embeddings.items())
            if (
                self._settings.semantic_cache_max_scan > 0
                and len(entries) > self._settings.semantic_cache_max_scan
            ):
                logger.debug(
                    "Semantic cache scan capped at %d entries (have %d)",
                    self._settings.semantic_cache_max_scan,
                    len(entries),
                )
                entries = entries[: self._settings.semantic_cache_max_scan]

            for q_hash, emb_str in entries:
                emb = np.array(json.loads(str(emb_str)), dtype=float)

                # Cosine Similarity
                q_norm = np.linalg.norm(q_vec)
                emb_norm = np.linalg.norm(emb)
                if q_norm == 0 or emb_norm == 0:
                    continue
                score = float(np.dot(q_vec, emb) / (q_norm * emb_norm))

                if score > best_score:
                    best_score = score
                    # Rebuild the versioned answer key for this candidate
                    # using the pre-computed query hash.
                    best_answer_key = self._build_cache_key_from_hash(
                        str(q_hash), scope_hash, semantic=True
                    )

            if best_score >= self._settings.semantic_cache_threshold:
                logger.info("L2 Cache Hit (score: %.3f) for query: %s...", best_score, query[:30])
                if best_answer_key:
                    result = self._redis.get(best_answer_key)
                    if result is not None:
                        return FinalResponse.model_validate_json(result)
                    return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("L2 cache read failed (treating as miss): %s", exc)
        return None

    def set_semantic(
        self,
        query: str,
        query_embedding: list[float],
        response: FinalResponse,
        user_context: UserContext,
    ) -> None:
        """Store an answer and its embedding in the L2 cache."""
        if self._redis is None or not response:
            return
        try:
            scope_hash = self._get_auth_scope_hash(user_context)
            query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()

            # Store the answer.
            key = self._build_cache_key(query, scope_hash, semantic=True)
            self._redis.setex(key, self._ttl, response.model_dump_json())

            # Store the embedding for future similarity searches.
            scope_key = f"scope_embeddings:{scope_hash}"
            self._redis.hset(scope_key, query_hash, json.dumps(query_embedding))
            # Set TTL on the scope index as well.
            self._redis.expire(scope_key, self._ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("L2 cache write failed (skipping): %s", exc)

    def ping(self) -> bool:
        """Return True if Redis is reachable and caching is enabled."""
        if self._redis is None:
            return False
        try:
            return bool(self._redis.ping())
        except Exception:  # noqa: BLE001
            return False

    # -- internals ---------------------------------------------------------

    def _get_auth_scope_hash(self, user_context: UserContext) -> str:
        """Create a stable hash of the user's security scope.

        Two users with the same roles, department, and tenant should
        have the same hash, as they are authorized to see the same data.
        """
        # Sort roles to ensure stable hashing.
        scope_string = (
            f"{user_context.tenant_id}|"
            f"{','.join(sorted(user_context.roles))}|"
            f"{user_context.department}"
        )
        return hashlib.sha256(scope_string.encode()).hexdigest()

    def _build_cache_key(self, query: str, scope_hash: str, semantic: bool = False) -> str:
        """Build a namespaced cache key with version stamps.

        Format:
        ``cache:{corpus}:{model}:{prompt}:{scope}:{type}:{query_hash}``

        The version stamps are baked into the key so bumping any of them
        invalidates the affected cache cohort without a manual Redis flush.
        """
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
        return self._build_cache_key_from_hash(query_hash, scope_hash, semantic=semantic)

    def _build_cache_key_from_hash(
        self, query_hash: str, scope_hash: str, semantic: bool = False
    ) -> str:
        """Build a namespaced cache key from a pre-computed query hash.

        Private helper used by the semantic-cache lookup path, where the
        candidate query hash is already available from the scope index.
        """
        cache_type = "semantic" if semantic else "exact"
        return (
            f"cache:{self._settings.corpus_version}:"
            f"{self._settings.embedding_model}:"
            f"{self._settings.cache_prompt_version}:"
            f"{scope_hash}:{cache_type}:{query_hash}"
        )
