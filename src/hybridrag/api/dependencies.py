"""Singleton wiring for the FastAPI app.

The retriever, embeddings, and assistant are constructed once at lifespan
startup so the production request path never pays the per-request
initialization cost.
"""

from __future__ import annotations

from typing import Any

from hybridrag.assistant import SecureCorpAssistant
from hybridrag.config import Settings


class AppState:
    """Container for app-wide singletons.

    Attached to ``app.state`` during FastAPI's lifespan so route handlers
    can fetch them via ``request.app.state``.
    """

    settings: Settings
    assistant: SecureCorpAssistant
    retriever: Any  # HybridRetriever — kept as Any to avoid a hard import here


def get_assistant(state: Any) -> SecureCorpAssistant:
    """Return the singleton :class:`SecureCorpAssistant` from app state."""
    assistant: SecureCorpAssistant = state.assistant
    return assistant


def get_retriever(state: Any) -> Any:
    """Return the singleton ``HybridRetriever`` from app state."""
    retriever: Any = state.retriever
    return retriever


def get_settings_from_state(state: Any) -> Settings:
    """Return the cached :class:`Settings` from app state."""
    settings: Settings = state.settings
    return settings
