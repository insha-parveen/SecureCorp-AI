"""Evidence preparation for LLM generation.

This module converts retrieved ``RankedChunk`` objects into a structured context block
that the LLM can use to generate grounded answers with valid citations.
"""

from collections.abc import Sequence

from hybridrag.domain import RankedChunk


def format_evidence(evidence: Sequence[RankedChunk]) -> str:
    """Turn a list of ranked chunks into a numbered context block.

    Each chunk is prefixed with its rank and identifier so the LLM can
    create unambiguous citations (e.g., '[1]' or 'Source: HR-001').
    """
    if not evidence:
        return "No relevant evidence was found in the knowledge base."

    lines = []
    for rank, item in enumerate(evidence, start=1):
        chunk = item.chunk
        # Include section title if available to give the LLM more structural context
        header = f" [{chunk.section_title}]" if chunk.section_title else ""
        line = f"[{rank}] {chunk.chunk_id}{header}: {chunk.text}"
        lines.append(line)

    return "\n\n".join(lines)


def create_generation_prompt(
    query: str,
    context: str,
    *,
    streaming: bool = False,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Wrap the query and evidence into a final prompt for the LLM.

    Args:
        query: The user's natural-language question.
        context: The formatted evidence block.
        streaming: When True, instructs the model to emit prose with inline
            ``[N]`` citations (e.g., ``[1]``, ``[2]``) instead of a JSON
            envelope. The streaming path cannot parse JSON incrementally,
            so inline citations are extracted from the assembled text.
        history: Optional list of previous {query, answer} pairs in the session.

    Returns:
        The full prompt string.
    """
    history_block = ""
    if history:
        history_lines = [f"User: {h['query']}\nAssistant: {h['answer']}" for h in history]
        history_block = "Conversation History:\n" + "\n---\n".join(history_lines) + "\n\n"

    if streaming:
        return (
            f"{history_block}"
            f"Context evidence:\n{'-' * 20}\n{context}\n{'-' * 20}\n\n"
            f"Question: {query}\n\n"
            f"Instructions:\n"
            f"1. Answer the question using ONLY the provided evidence.\n"
            f"2. If the answer is not in the evidence, state that you do not know.\n"
            f"3. Cite the evidence you use inline as [N] where N is the rank "
            f"of the evidence (e.g., [1], [2]).\n"
            f"4. Write in plain prose — no JSON, no markdown code fences.\n"
        )

    return (
        f"{history_block}"
        f"Context evidence:\n{'-' * 20}\n{context}\n{'-' * 20}\n\n"
        f"Question: {query}\n\n"
        f"Instructions:\n"
        f"1. Answer the question using ONLY the provided evidence.\n"
        f"2. If the answer is not in the evidence, state that you do not know.\n"
        f"3. Provide the output as a valid JSON object with the following keys:\n"
        f'   - "answer": The concise, professional answer string.\n'
        f'   - "citations": A list of integers representing the [rank] of the evidence used.\n'
        f"4. Return ONLY the raw JSON — no markdown code fences.\n"
    )
