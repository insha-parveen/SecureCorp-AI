"""Unit tests for configuration invariants.

The chunk-budget validator is a correctness guard, not a style check: an
embedding model silently truncates anything past its input limit, so a
misconfigured chunk size loses evidence with no error anywhere in the pipeline.
"""

import pytest

from hybridrag.config import Settings


class TestChunkBudgetValidator:
    def test_default_settings_fit_the_embedding_model(self) -> None:
        settings = Settings()
        worst_case = settings.chunk_overlap_tokens + settings.chunk_max_tokens
        assert worst_case <= settings.embedding_max_tokens - 2

    def test_oversized_chunks_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="silently truncated"):
            Settings(chunk_max_tokens=600, chunk_overlap_tokens=60, embedding_max_tokens=512)

    def test_overlap_counts_towards_the_budget(self) -> None:
        # max alone fits; max + overlap does not.
        Settings(chunk_max_tokens=500, chunk_overlap_tokens=10, embedding_max_tokens=512)
        with pytest.raises(ValueError, match="silently truncated"):
            Settings(chunk_max_tokens=500, chunk_overlap_tokens=11, embedding_max_tokens=512)

    def test_a_larger_model_permits_larger_chunks(self) -> None:
        settings = Settings(
            chunk_max_tokens=900, chunk_overlap_tokens=100, embedding_max_tokens=1024
        )
        assert settings.chunk_max_tokens == 900
