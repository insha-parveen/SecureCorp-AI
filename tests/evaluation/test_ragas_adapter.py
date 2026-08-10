"""Unit tests for the Phase 8 RAGAS adapter.

The adapter is verified with a fake ``GenerationProvider`` / ``EmbeddingProvider``
so the test never imports ragas, datasets, or any network code. The runner is
exercised only at the module-import + adapter level — ragas itself is exercised
in scripts/run_ragas.py where the optional dependency lives.
"""

from __future__ import annotations

from typing import Any

import pytest

from hybridrag.evaluation.ragas_adapter import ProjectRagasEmbeddings, ProjectRagasLLM


class FakeLLM:
    """Stand-in for ``GenerationProvider`` — records prompts, returns canned text."""

    def __init__(self, canned_text: str = "canned response", model: str = "fake-model") -> None:
        self._canned = canned_text
        self._model = model
        self.calls: list[dict[str, Any]] = []

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str, system_prompt: str | None = None) -> Any:
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        # Return an object shaped like ``GenerationResponse``
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class _R:
            text: str
            model: str
            usage: dict[str, int]

        return _R(
            text=self._canned, model=self._model, usage={"prompt_tokens": 1, "completion_tokens": 1}
        )


class FakeEmbeddings:
    """Stand-in for ``EmbeddingProvider``."""

    def __init__(self, dim: int = 4, model: str = "fake-emb") -> None:
        self._dim = dim
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))] + [0.0] * (self._dim - 1)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


def test_ragas_llm_delegates_to_provider_and_returns_n_copies() -> None:
    fake = FakeLLM(canned_text="answer")
    adapter = ProjectRagasLLM(fake)  # type: ignore[arg-type]

    out = adapter.generate_text("hello", n=3)
    assert out == ["answer", "answer", "answer"]
    # Single underlying call regardless of n (project provider doesn't fan out).
    assert len(fake.calls) == 1
    assert fake.calls[0]["prompt"] == "hello"


def test_ragas_llm_propagates_system_prompt_when_supplied() -> None:
    fake = FakeLLM()
    adapter = ProjectRagasLLM(fake)  # type: ignore[arg-type]

    adapter.generate_text("hi", system_prompt="be terse")
    assert fake.calls[0]["system_prompt"] == "be terse"


def test_ragas_llm_handles_no_system_prompt() -> None:
    fake = FakeLLM()
    adapter = ProjectRagasLLM(fake)  # type: ignore[arg-type]

    adapter.generate_text("hi")
    assert fake.calls[0]["system_prompt"] is None


def test_ragas_llm_model_name_is_provider_model_name() -> None:
    fake = FakeLLM(model="llama-test")
    adapter = ProjectRagasLLM(fake)  # type: ignore[arg-type]
    assert adapter.model_name == "llama-test"


def test_ragas_embeddings_query_returns_float_list() -> None:
    fake = FakeEmbeddings(dim=4)
    adapter = ProjectRagasEmbeddings(fake)  # type: ignore[arg-type]
    vec = adapter.embed_query("hello")
    assert isinstance(vec, list)
    assert vec[0] == pytest.approx(5.0)  # len("hello") == 5
    assert len(vec) == 4


def test_ragas_embeddings_documents_returns_n_lists() -> None:
    fake = FakeEmbeddings(dim=3)
    adapter = ProjectRagasEmbeddings(fake)  # type: ignore[arg-type]
    vecs = adapter.embed_documents(["abc", "de"])
    assert len(vecs) == 2
    assert vecs[0][0] == pytest.approx(3.0)
    assert vecs[1][0] == pytest.approx(2.0)


def test_ragas_embeddings_model_name_is_provider_model_name() -> None:
    fake = FakeEmbeddings(model="minilm-fake")
    adapter = ProjectRagasEmbeddings(fake)  # type: ignore[arg-type]
    assert adapter.model_name == "minilm-fake"


def test_ragas_llm_is_finished_returns_true() -> None:
    fake = FakeLLM()
    adapter = ProjectRagasLLM(fake)  # type: ignore[arg-type]
    assert adapter.is_finished(["anything"]) is True
