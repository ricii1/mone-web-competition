from dataclasses import dataclass

import pymupdf as fitz


class PdfParsingError(Exception):
    pass


@dataclass
class HeadingSpan:
    page: int
    text: str
    size: float


@dataclass
class ParsedPdf:
    pages: list[str]
    toc: list[tuple[int, str, int]]
    headings: list[HeadingSpan]


def parse_pdf(file_path: str) -> ParsedPdf:
    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise PdfParsingError(f"Gagal membuka PDF: {exc}") from exc

    if doc.page_count == 0:
        raise PdfParsingError("PDF tidak memiliki halaman")

    pages: list[str] = []
    all_sizes: list[float] = []
    page_spans: list[list[tuple[str, float]]] = []

    for page in doc:
        text = page.get_text("text")
        pages.append(text)

        spans: list[tuple[str, float]] = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span["text"].strip()
                    if span_text:
                        spans.append((span_text, span["size"]))
                        all_sizes.append(span["size"])
        page_spans.append(spans)

    if not "".join(pages).strip():
        raise PdfParsingError("PDF tidak berisi teks yang bisa diekstrak")

    body_size = sorted(all_sizes)[len(all_sizes) // 2] if all_sizes else 0.0
    headings: list[HeadingSpan] = []
    for page_index, spans in enumerate(page_spans):
        for span_text, size in spans:
            word_count = len(span_text.split())
            if size >= body_size * 1.25 and 0 < word_count <= 15:
                headings.append(HeadingSpan(page=page_index, text=span_text, size=size))

    toc = doc.get_toc()
    return ParsedPdf(pages=pages, toc=toc, headings=headings)
