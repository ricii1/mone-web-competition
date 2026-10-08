from app.rag.chunking import chunk_parsed_pdf
from app.rag.parsing import HeadingSpan, ParsedPdf


def test_chunk_by_toc_uses_section_titles():
    parsed = ParsedPdf(
        pages=["Halaman 1 isi bab satu", "Halaman 2 lanjutan bab satu", "Halaman 3 bab dua"],
        toc=[(1, "Bab Satu", 1), (1, "Bab Dua", 3)],
        headings=[],
    )
    chunks = chunk_parsed_pdf(parsed)
    assert [c.section_title for c in chunks] == ["Bab Satu", "Bab Dua"]
    assert chunks[0].page_start == 0
    assert chunks[0].page_end == 1
    assert chunks[1].page_start == 2


def test_chunk_by_font_headings_when_no_toc():
    parsed = ParsedPdf(
        pages=["Judul Satu\nIsi materi pertama", "Judul Dua\nIsi materi kedua"],
        toc=[],
        headings=[
            HeadingSpan(page=0, text="Judul Satu", size=20.0),
            HeadingSpan(page=1, text="Judul Dua", size=20.0),
        ],
    )
    chunks = chunk_parsed_pdf(parsed)
    assert [c.section_title for c in chunks] == ["Judul Satu", "Judul Dua"]


def test_chunk_fixed_size_fallback_when_no_structure():
    long_text = " ".join(f"kata{i}" for i in range(1200))
    parsed = ParsedPdf(pages=[long_text], toc=[], headings=[])
    chunks = chunk_parsed_pdf(parsed)
    assert len(chunks) > 1
    assert all(c.section_title is None for c in chunks)
    assert all(len(c.content.split()) <= 500 for c in chunks)


def test_chunk_fixed_size_handles_short_text():
    parsed = ParsedPdf(pages=["hanya sedikit kata di sini"], toc=[], headings=[])
    chunks = chunk_parsed_pdf(parsed)
    assert len(chunks) == 1
    assert chunks[0].content == "hanya sedikit kata di sini"
