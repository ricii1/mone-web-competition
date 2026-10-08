from dataclasses import dataclass

from app.rag.parsing import ParsedPdf

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
    entries = sorted(parsed.toc, key=lambda e: e[2])
    chunks: list[Chunk] = []
    total_pages = len(parsed.pages)

    for i, (_level, title, start_page_1indexed) in enumerate(entries):
        start_page = max(start_page_1indexed - 1, 0)
        if i + 1 < len(entries):
            next_start_page = max(entries[i + 1][2] - 1, 0)
            end_page = max(next_start_page - 1, start_page)
        else:
            end_page = total_pages - 1
        end_page = min(end_page, total_pages - 1)
        content = "\n".join(parsed.pages[start_page : end_page + 1]).strip()
        if content:
            chunks.append(
                Chunk(
                    section_title=title, content=content, page_start=start_page, page_end=end_page
                )
            )
    return chunks or _chunk_fixed_size(parsed)


def _chunk_by_headings(parsed: ParsedPdf) -> list[Chunk]:
    headings = sorted(parsed.headings, key=lambda h: h.page)
    chunks: list[Chunk] = []
    total_pages = len(parsed.pages)

    for i, heading in enumerate(headings):
        start_page = heading.page
        end_page = headings[i + 1].page if i + 1 < len(headings) else total_pages - 1
        end_page = max(end_page, start_page)
        content = "\n".join(parsed.pages[start_page : end_page + 1]).strip()
        if content:
            chunks.append(
                Chunk(
                    section_title=heading.text,
                    content=content,
                    page_start=start_page,
                    page_end=end_page,
                )
            )
    return chunks or _chunk_fixed_size(parsed)


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
