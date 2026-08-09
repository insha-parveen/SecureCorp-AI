import pytest

from hybridrag.domain import Chunk, RankedChunk
from hybridrag.generation.generator import get_generator


def test_abstention_with_irrelevant_evidence():
    # 1. Setup irrelevant evidence
    irrelevant_chunks = [
        Chunk(
            chunk_id="C1",
            document_id="D1",
            document_version="v1",
            text="The weather in Lucknow is sunny.",
            chunk_index=0,
            token_count=10,
            content_hash="h1",
            source_type="policy",
            document_type="policy",
            classification="public",
            allowed_roles=("employee",),
            effective_date=None,
            metadata={},
        )
    ]
    evidence = [
        RankedChunk(chunk=c, score=1.0, rank=1, retriever="bm25") for c in irrelevant_chunks
    ]

    # 2. Use the real generator (which uses the configured LLM)
    generator = get_generator()

    # 3. Ask a question that is NOT answered by the evidence
    query = "What is the company's remote work policy?"
    response = generator.generate_answer(query, evidence)

    print(f"\nQuery: {query}")
    print(f"Answer: {response.answer}")

    # We expect the model to abstain (say "I don't know" or similar)
    # and NOT return citations for irrelevant text.
    assert (
        "do not know" in response.answer.lower()
        or "insufficient information" in response.answer.lower()
    )
    assert len(response.citations) == 0


if __name__ == "__main__":
    pytest.main([__file__])
