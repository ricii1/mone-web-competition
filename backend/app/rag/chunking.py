from bisect import bisect_right
from dataclasses import dataclass

from app.rag.parsing import HeadingSpan, ParsedPdf, find_heading_offset

CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50


@dataclass
class Chunk:
    section_title: str | None
    content: str
    page_start: int
    page_end: int


def chunk_parsed_pdf(parsed: ParsedPdf) -> list[Chunk]:
    if parsed.toc:
        return _chunk_by_toc(parsed)
    if parsed.headings:
        return _chunk_by_headings(parsed)
    return _chunk_fixed_size(parsed)


def _chunk_by_toc(parsed: ParsedPdf) -> list[Chunk]:
    entries = [entry for entry in parsed.toc if 1 <= entry[2] <= len(parsed.pages)]
    boundaries = parsed.toc_headings or [
        HeadingSpan(
            page=page_number - 1,
            text=title,
            size=0,
            offset=find_heading_offset(parsed.pages[page_number - 1], title) or 0,
        )
        for _, title, page_number in entries
    ]
    # Unrelated bookmarks at the same location cannot define separate sections safely.
    positions: dict[tuple[int, int | None], int] = {}
    for boundary, entry in zip(boundaries, entries, strict=False):
        position = (boundary.page, boundary.offset)
        if position in positions and positions[position] == entry[0]:
            return _chunk_by_headings(parsed) if parsed.headings else _chunk_fixed_size(parsed)
        positions[position] = entry[0]
    return _chunk_sections(parsed, boundaries) or _chunk_fixed_size(parsed)


def _chunk_by_headings(parsed: ParsedPdf) -> list[Chunk]:
    return _chunk_sections(parsed, parsed.headings) or _chunk_fixed_size(parsed)


def _chunk_sections(parsed: ParsedPdf, headings: list[HeadingSpan]) -> list[Chunk]:
    text = "\n".join(parsed.pages)
    page_starts: list[int] = []
    position = 0
    for page in parsed.pages:
        page_starts.append(position)
        position += len(page) + 1
    boundaries: dict[int, HeadingSpan] = {}
    for heading in headings:
        if not 0 <= heading.page < len(parsed.pages):
            continue
        offset = heading.offset
        if offset is None:
            offset = find_heading_offset(parsed.pages[heading.page], heading.text) or 0
        offset = max(0, min(offset, len(parsed.pages[heading.page])))
        boundaries[page_starts[heading.page] + offset] = heading
    ordered = sorted(boundaries.items())
    chunks = []
    for index, (start, heading) in enumerate(ordered):
        # Preserve any introduction preceding the first heading without creating a new level.
        if index == 0:
            start = 0
        end = ordered[index + 1][0] if index + 1 < len(ordered) else len(text)
        source = text[start:end]
        content = source.strip()
        if not content:
            continue
        first = start + len(source) - len(source.lstrip())
        last = start + len(source.rstrip()) - 1
        chunks.append(
            Chunk(
                section_title=heading.text,
                content=content,
                page_start=bisect_right(page_starts, first) - 1,
                page_end=bisect_right(page_starts, last) - 1,
            )
        )
    return chunks


def _chunk_fixed_size(parsed: ParsedPdf) -> list[Chunk]:
    words_with_page: list[tuple[str, int]] = []
    for page_index, page_text in enumerate(parsed.pages):
        for word in page_text.split():
            words_with_page.append((word, page_index))

    chunks: list[Chunk] = []
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
    for start in range(0, len(words_with_page), step):
        window = words_with_page[start : start + CHUNK_SIZE_WORDS]
        if not window:
            continue
        content = " ".join(w for w, _ in window)
        chunks.append(
            Chunk(
                section_title=None,
                content=content,
                page_start=window[0][1],
                page_end=window[-1][1],
            )
        )
        if start + CHUNK_SIZE_WORDS >= len(words_with_page):
            break
    return chunks
