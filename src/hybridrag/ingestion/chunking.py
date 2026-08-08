"""Document-type-aware hierarchical chunking.

The corpus is heterogeneous, so one fixed-size splitter would be wrong for
most of it (CLAUDE.md §9). Chunking therefore runs in two stages:

1. **Atomize** — a per-source-type strategy breaks the body into *atoms*:
   the smallest units that must never be split across chunks. What counts as
   an atom differs by document type:

   ===================  ==========================================
   source type          atom
   ===================  ==========================================
   policy / kb / jira   a paragraph within a heading section
   github               a paragraph within a heading section
   email                the whole message (they are short and
                        self-contained: header block + body)
   meeting              one timestamped speaker turn
   slack                one timestamped message
   ===================  ==========================================

2. **Pack** — atoms are greedily packed into chunks up to the configured token
   budget. A heading boundary ends the chunk once it has reached
   ``min_tokens``; below that, consecutive small sections merge rather than
   emitting a swarm of tiny chunks (a heading-dense policy would otherwise
   average ~80 tokens per chunk, hurting BM25 term statistics and embedding
   quality alike). Oversized single atoms are sentence-split as a last resort.

Overlap is applied only where it preserves continuity — inside a section or a
conversation — and never across a boundary. Merged text is therefore always
genuinely adjacent in the source document, and no text is ever duplicated
across a heading boundary. Chunks that span sections record every section
they cover in ``metadata["section_titles"]``.

Every chunk inherits the parent Document's authorization metadata verbatim.
That inheritance is the reason the "zero unauthorized chunks" invariant can be
enforced at the retrieval boundary: there is no chunk whose ``allowed_roles``
differ from the document it came from.
"""

from collections.abc import Callable, Iterable, Iterator

from hybridrag.domain import Chunk, Document, SourceType, content_hash, make_chunk_id
from hybridrag.ingestion.structure import parse_sections
from hybridrag.ingestion.tokenization import count_tokens, split_paragraphs, split_sentences

# ---------------------------------------------------------------------------
# Atoms
# ---------------------------------------------------------------------------


class Atom:
    """An indivisible unit of text plus the context needed to attribute it.

    ``boundary_key`` marks which section/conversation the atom belongs to. A
    change of key is a preferred chunk break and always stops overlap, though
    the packer may merge across one when the chunk is still under
    ``min_tokens``.
    """

    __slots__ = ("boundary_key", "section_title", "text", "tokens")

    def __init__(self, text: str, section_title: str | None, boundary_key: str) -> None:
        self.text = text
        self.section_title = section_title
        self.boundary_key = boundary_key
        self.tokens = count_tokens(text)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Atom(section={self.section_title!r}, tokens={self.tokens})"


def _section_atoms(body: str) -> list[Atom]:
    """Heading-aware atomization: paragraphs scoped to their heading section.

    Used for policies, SOPs, knowledge-base articles, Jira issues and GitHub
    artifacts — everything whose meaning is carried by its heading structure.
    A numbered procedure written as consecutive lines stays in one atom
    because ``split_paragraphs`` only breaks on blank lines.
    """
    atoms: list[Atom] = []
    for index, section in enumerate(parse_sections(body)):
        title = section.display_title
        # Include the heading trail in the boundary key so two sections that
        # happen to share a title still form separate boundaries.
        key = f"section:{index}"
        for paragraph in split_paragraphs(section.text):
            atoms.append(Atom(paragraph, title, key))
    return atoms


def _whole_document_atoms(body: str) -> list[Atom]:
    """Email atomization: paragraphs that all share one boundary.

    Emails are short and self-contained; the header block (From/To/Subject)
    is meaningful context for the body, so everything stays packable together
    and short emails become a single chunk.
    """
    sections = parse_sections(body)
    title = sections[0].display_title if sections else None
    return [Atom(p, title, "document") for p in split_paragraphs(body)]


def _turn_atoms(body: str, section_label: str) -> list[Atom]:
    """Conversation atomization: one atom per speaker turn / message.

    Meeting transcripts and Slack threads are sequences of attributed turns.
    Splitting mid-turn would strip a statement from its speaker, so each turn
    is atomic. Turns share a boundary key, letting consecutive turns pack into
    one chunk with overlap that preserves conversational context.
    """
    atoms: list[Atom] = []
    for section in parse_sections(body):
        title = section.display_title or section_label
        for paragraph in split_paragraphs(section.text):
            atoms.append(Atom(paragraph, title, "conversation"))
    return _merge_speaker_turns(atoms)


def _merge_speaker_turns(atoms: list[Atom]) -> list[Atom]:
    """Join an attribution line to the message that follows it.

    Transcripts and Slack exports write the timestamp/speaker as its own
    blank-line-separated block:

        **10:03**
        **Sunita Rao:**

        Thanks, Arvind. ...

    Left alone, the attribution would become an orphan atom and could land in
    a different chunk than the words it attributes.
    """
    merged: list[Atom] = []
    pending: list[str] = []
    for atom in atoms:
        if _is_attribution(atom.text):
            pending.append(atom.text)
            continue
        text = "\n".join([*pending, atom.text]) if pending else atom.text
        merged.append(Atom(text, atom.section_title, atom.boundary_key))
        pending.clear()
    if pending:  # trailing attribution with no message body
        last = atoms[-1]
        merged.append(Atom("\n".join(pending), last.section_title, last.boundary_key))
    return merged


def _is_attribution(text: str) -> bool:
    """Heuristic: a short all-bold block is a timestamp/speaker header."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines or len(lines) > 3:
        return False
    return all(line.startswith("**") and line.endswith("**") for line in lines)


_ATOMIZERS: dict[SourceType, Callable[[str], list[Atom]]] = {
    SourceType.EMAIL: _whole_document_atoms,
    SourceType.MEETING: lambda body: _turn_atoms(body, "Transcript"),
    SourceType.SLACK: lambda body: _turn_atoms(body, "Thread"),
}


def atomize(body: str, source_type: SourceType) -> list[Atom]:
    """Break a body into indivisible atoms using the source-type strategy."""
    atomizer = _ATOMIZERS.get(source_type)
    return atomizer(body) if atomizer else _section_atoms(body)


# ---------------------------------------------------------------------------
# Packing
# ---------------------------------------------------------------------------


def _split_oversized(atom: Atom, max_tokens: int) -> list[Atom]:
    """Break a single over-budget atom on sentence boundaries.

    Only reached when one paragraph or speaker turn exceeds the hard limit on
    its own, at which point some split is unavoidable.
    """
    pieces: list[Atom] = []
    buffer: list[str] = []
    tokens = 0
    for sentence in split_sentences(atom.text):
        sentence_tokens = count_tokens(sentence)
        if buffer and tokens + sentence_tokens > max_tokens:
            pieces.append(Atom(" ".join(buffer), atom.section_title, atom.boundary_key))
            buffer, tokens = [], 0
        buffer.append(sentence)
        tokens += sentence_tokens
    if buffer:
        pieces.append(Atom(" ".join(buffer), atom.section_title, atom.boundary_key))
    return pieces or [atom]


def _overlap_atoms(atoms: list[Atom], overlap_tokens: int) -> list[Atom]:
    """Return trailing atoms from a packed chunk to prepend to the next one."""
    if overlap_tokens <= 0:
        return []
    carried: list[Atom] = []
    total = 0
    for atom in reversed(atoms):
        if total + atom.tokens > overlap_tokens:
            break
        carried.insert(0, atom)
        total += atom.tokens
    # Never carry the entire chunk forward — that would make no progress.
    return carried if len(carried) < len(atoms) else carried[1:]


class PackedChunk:
    """The text of one packed chunk plus the sections it was drawn from."""

    __slots__ = ("section_titles", "text")

    def __init__(self, text: str, section_titles: list[str | None]) -> None:
        self.text = text
        self.section_titles = section_titles

    @property
    def section_title(self) -> str | None:
        """Primary attribution: the section the chunk *starts* in."""
        return self.section_titles[0] if self.section_titles else None


def pack_atoms(
    atoms: Iterable[Atom],
    *,
    target_tokens: int,
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int = 0,
) -> Iterator[PackedChunk]:
    """Greedily pack atoms into chunks.

    An atom that would push the buffer past ``target_tokens`` starts the next
    chunk, so emitted chunks stay at or under the target. Atoms larger than
    ``max_tokens`` on their own are sentence-split first.

    A change of boundary key (a new heading section) flushes the chunk *only
    once it holds at least* ``min_tokens``. Without that rule a heading-dense
    policy produces a swarm of 20-token chunks, which wrecks both BM25 term
    statistics and dense-embedding quality. Consecutive small sections are
    therefore merged, and every section they span is recorded so citations can
    still name the right part of the document.

    Overlap is never carried across a boundary, so merged text is always
    genuinely adjacent in the source document and never duplicated.
    """
    buffer: list[Atom] = []
    tokens = 0
    boundary: str | None = None

    def flush() -> PackedChunk | None:
        if not buffer:
            return None
        text = "\n\n".join(a.text for a in buffer).strip()
        if not text:
            return None
        titles: list[str | None] = []
        for atom in buffer:
            if not titles or titles[-1] != atom.section_title:
                titles.append(atom.section_title)
        return PackedChunk(text, titles)

    for atom in atoms:
        for piece in _split_oversized(atom, max_tokens) if atom.tokens > max_tokens else [atom]:
            crossed = boundary is not None and piece.boundary_key != boundary
            over_target = tokens + piece.tokens > target_tokens
            if buffer and (over_target or (crossed and tokens >= min_tokens)):
                packed = flush()
                if packed:
                    yield packed
                # Overlap only continues a section; it never spans a boundary.
                carried = [] if crossed else _overlap_atoms(buffer, overlap_tokens)
                buffer = list(carried)
                tokens = sum(a.tokens for a in buffer)
            buffer.append(piece)
            tokens += piece.tokens
            boundary = piece.boundary_key

    packed = flush()
    if packed:
        yield packed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chunk_document(
    document: Document,
    body: str,
    *,
    target_tokens: int,
    max_tokens: int,
    overlap_tokens: int,
    min_tokens: int = 0,
) -> list[Chunk]:
    """Chunk one document, inheriting all authorization/provenance metadata.

    Chunk IDs are ``{document_id}:{version}:{index:04d}`` — stable and
    reproducible for a given body, which is what makes RRF fusion and citation
    resolution work across re-ingestion.
    """
    atoms = atomize(body, document.source_type)
    chunks: list[Chunk] = []
    packed = pack_atoms(
        atoms,
        target_tokens=target_tokens,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        min_tokens=min_tokens,
    )
    for index, item in enumerate(packed):
        text = item.text
        # Record every section a merged chunk spans; retrieval debugging and
        # citation rendering both need more than the first heading.
        spanned = [title for title in item.section_titles if title]
        metadata: dict[str, object] = {
            "title": document.title,
            "source_uri": document.source_uri,
        }
        if len(spanned) > 1:
            metadata["section_titles"] = spanned
        chunks.append(
            Chunk(
                chunk_id=make_chunk_id(document.document_id, document.document_version, index),
                document_id=document.document_id,
                document_version=document.document_version,
                text=text,
                chunk_index=index,
                token_count=count_tokens(text),
                content_hash=content_hash(text),
                section_title=item.section_title,
                page_number=None,  # Markdown corpus has no page boundaries
                # --- inherited authorization / provenance ---
                source_type=document.source_type,
                document_type=document.document_type,
                department=document.department,
                classification=document.classification,
                allowed_roles=document.allowed_roles,
                allowed_departments=document.allowed_departments,
                owner_user_id=document.owner_user_id,
                tenant_id=document.tenant_id,
                effective_date=document.effective_date,
                status=document.status,
                metadata=metadata,
            )
        )
    return chunks
