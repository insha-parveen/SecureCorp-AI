"""Evidence preparation for LLM generation.

This module converts retrieved ``RankedChunk`` objects into a structured context block
that the LLM can use to generate grounded answers with valid citations.
"""

from collections.abc import Sequence

from hybridrag.domain import RankedChunk
from hybridrag.generation.abstention import ABSTENTION_SENTENCE


def format_evidence(evidence: Sequence[RankedChunk]) -> str:
    """Turn a list of ranked chunks into a numbered context block.

    Each chunk is prefixed with a ``[[N]]`` sentinel marker (double brackets)
    so the LLM can cite it unambiguously. Double brackets are used because the
    chunk text itself frequently contains single-bracket / markdown content
    (tables, ``[Section]`` headers, ``[1]``-style footnotes); a bare ``[N]``
    rank marker collides with those and reasoning models then cite a number
    scraped from inside the text instead of the rank. ``[[N]]`` does not occur
    in the corpus, so it is a clean citation anchor.
    """
    if not evidence:
        return "No relevant evidence was found in the knowledge base."

    lines = []
    for rank, item in enumerate(evidence, start=1):
        chunk = item.chunk
        # Include section title if available to give the LLM more structural context
        header = f" [{chunk.section_title}]" if chunk.section_title else ""
        line = f"[[{rank}]] (source {chunk.chunk_id}){header}: {chunk.text}"
        lines.append(line)

    return "\n\n".join(lines)


def create_generation_prompt(
    query: str,
    context: str,
    *,
    streaming: bool = False,
    history: list[dict[str, str]] | None = None,
    evidence_count: int | None = None,
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
        evidence_count: Number of evidence items (their ranks run 1..N). Used to
            tell the model the exact valid citation range, which stops
            reasoning models from citing document ids / years instead of ranks.

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
            f"2. If the evidence does not answer the question, reply EXACTLY with "
            f'this sentence: "{ABSTENTION_SENTENCE}"\n'
            f"3. Cite the evidence you use inline as [[N]] where N is the number\n"
            f"   in the [[N]] marker at the start of the evidence line "
            f"(e.g., [[1]], [[2]]).\n"
            f"4. Write in plain prose — no JSON, no markdown code fences.\n"
        )

    n = evidence_count if evidence_count is not None else 0
    valid_range = (
        f"Valid citation numbers are the integers 1 to {n} ONLY."
        if n
        else "There is no evidence, so citations must be an empty list."
    )
    return (
        f"{history_block}"
        f"Context evidence:\n{'-' * 20}\n{context}\n{'-' * 20}\n\n"
        f"Question: {query}\n\n"
        f"Instructions:\n"
        f"1. Answer the question using ONLY the provided evidence.\n"
        f'2. If the evidence does not answer the question, set "answer" EXACTLY to:\n'
        f'   "{ABSTENTION_SENTENCE}" and "citations" to [].\n'
        f"3. Provide the output as a valid JSON object with the following keys:\n"
        f'   - "answer": The concise, professional answer string.\n'
        f'   - "citations": A list of integers. Each integer N is the number\n'
        f"     inside a [[N]] marker at the START of an evidence line that you\n"
        f"     actually used — NOT a source id, year, or any number from inside\n"
        f"     the evidence text. {valid_range}\n"
        f'   Example: {{"answer": "...", "citations": [1, 3]}}\n'
        f"4. Return ONLY the raw JSON — no markdown code fences.\n"
    )
