"""Conversation history store for SecureCorp AI.

This module implements a Redis-backed store for chat history, allowing the
assistant to resolve anaphoras (e.g., 'it', 'they') and maintain context
across a session.

History is scoped by tenant, user, and session to ensure isolation.
"""

import json
import logging
from typing import Any

import redis

from hybridrag.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ConversationHistory:
    """Redis-backed store for session-based chat history."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._redis: Any = None
        if self._settings.cache_enabled:
            try:
                self._redis = redis.from_url(
                    self._settings.redis_url, decode_responses=True, socket_timeout=1
                )
            except Exception as exc:
                logger.warning("Redis unavailable for history; context disabled: %s", exc)
                self._redis = None

    def _build_key(self, tenant_id: str, user_id: str, session_id: str) -> str:
        return f"history:{tenant_id}:{user_id}:{session_id}"

    def add_message(
        self, tenant_id: str, user_id: str, session_id: str, query: str, answer: str
    ) -> None:
        """Append a query-answer pair to the session history."""
        if self._redis is None:
            return
        try:
            key = self._build_key(tenant_id, user_id, session_id)
            entry = json.dumps({"query": query, "answer": answer})
            # Use a list in Redis to keep the order.
            self._redis.rpush(key, entry)
            # Keep only the last N messages to avoid context window overflow.
            self._redis.ltrim(key, -10, -1)
            # Set expiry for the session (e.g., 24 hours).
            self._redis.expire(key, 86400)
        except Exception as exc:
            logger.warning("Failed to save chat history: %s", exc)

    def get_history(
        self, tenant_id: str, user_id: str, session_id: str, limit: int = 5
    ) -> list[dict[str, str]]:
        """Retrieve the most recent N messages from the session."""
        if self._redis is None:
            return []
        try:
            key = self._build_key(tenant_id, user_id, session_id)
            # Get the last 'limit' items.
            raw_history = self._redis.lrange(key, -limit, -1)
            return [json.loads(item) for item in raw_history]
        except Exception as exc:
            logger.warning("Failed to retrieve chat history: %s", exc)
            return []

    def clear_history(self, tenant_id: str, user_id: str, session_id: str) -> None:
        """Delete the session history."""
        if self._redis is None:
            return
        try:
            key = self._build_key(tenant_id, user_id, session_id)
            self._redis.delete(key)
        except Exception as exc:
            logger.warning("Failed to clear chat history: %s", exc)
