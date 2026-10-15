import re
from dataclasses import dataclass, field

import pymupdf as fitz


class PdfParsingError(Exception):
    pass


@dataclass
class HeadingSpan:
    page: int
    text: str
    size: float
    offset: int | None = None


@dataclass
class ParsedPdf:
    pages: list[str]
    toc: list[tuple[int, str, int]]
    headings: list[HeadingSpan]
    toc_headings: list[HeadingSpan] = field(default_factory=list)


@dataclass
class _TextLine:
    offset: int
    text: str
    size: float
    bottom: float
    block: int


def find_heading_offset(text: str, title: str) -> int | None:
    words = title.split()
    if not words:
        return None
    pattern = r"(?m)^[ \t]*" + r"\s+".join(re.escape(word) for word in words) + r"[ \t]*$"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.start() if match else None


def parse_pdf(file_path: str) -> ParsedPdf:
    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise PdfParsingError(f"Gagal membuka PDF: {exc}") from exc

    with doc:
        if doc.page_count == 0:
            raise PdfParsingError("PDF tidak memiliki halaman")
        pages: list[str] = []
        all_sizes: list[float] = []
        page_lines: list[list[_TextLine]] = []
        for page in doc:
            lines: list[_TextLine] = []
            offset = 0
            for block in page.get_text("dict", sort=True)["blocks"]:
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    text = ""
                    for index, span in enumerate(spans):
                        if index and text and span["text"]:
                            gap = span["bbox"][0] - spans[index - 1]["bbox"][2]
                            if (
                                gap > 0.1
                                and not text[-1].isspace()
                                and not span["text"][0].isspace()
                            ):
                                text += " "
                        text += span["text"]
                        if span["text"].strip():
                            all_sizes.append(span["size"])
                    text = text.rstrip()
                    if not text.strip():
                        continue
                    lines.append(
                        _TextLine(
                            offset=offset,
                            text=text,
                            size=max(span["size"] for span in spans),
                            bottom=line["bbox"][3],
                            block=block["number"],
                        )
                    )
                    offset += len(text) + 1
            pages.append("".join(f"{line.text}\n" for line in lines))
            page_lines.append(lines)

        if not "".join(pages).strip():
            raise PdfParsingError("PDF tidak berisi teks yang bisa diekstrak")

        body_size = sorted(all_sizes)[len(all_sizes) // 2] if all_sizes else 0.0
        headings: list[HeadingSpan] = []
        for page_index, lines in enumerate(page_lines):
            previous_block = None
            for line in lines:
                word_count = len(line.text.split())
                if line.size < body_size * 1.25 or not 0 < word_count <= 15:
                    previous_block = None
                    continue
                if previous_block == line.block and headings[-1].page == page_index:
                    combined = f"{headings[-1].text} {line.text.strip()}"
                    if len(combined.split()) <= 15:
                        headings[-1].text = combined
                        continue
                headings.append(
                    HeadingSpan(
                        page=page_index,
                        text=line.text.strip(),
                        size=line.size,
                        offset=line.offset,
                    )
                )
                previous_block = line.block

        toc = []
        toc_headings = []
        for level, title, page_number, destination in doc.get_toc(simple=False):
            if not 1 <= page_number <= len(pages):
                continue
            page_index = page_number - 1
            offset = find_heading_offset(pages[page_index], title)
            if offset is None:
                point = destination.get("to")
                target_y = getattr(point, "y", 0)
                offset = next(
                    (line.offset for line in page_lines[page_index] if line.bottom > target_y), 0
                )
            toc.append((level, title, page_number))
            toc_headings.append(HeadingSpan(page_index, title, 0, offset))
        return ParsedPdf(pages=pages, toc=toc, headings=headings, toc_headings=toc_headings)
