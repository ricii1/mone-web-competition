import pymupdf
import pytest

from app.rag.parsing import PdfParsingError, parse_pdf


def _make_pdf(path: str, pages_text: list[str], toc: list[list] | None = None) -> None:
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    if toc:
        doc.set_toc(toc)
    doc.save(path)
    doc.close()


def test_parse_pdf_extracts_text_and_toc(tmp_path):
    pdf_path = tmp_path / "materi.pdf"
    _make_pdf(
        str(pdf_path), ["Bab satu isi", "Bab dua isi"], toc=[[1, "Bab Satu", 1], [1, "Bab Dua", 2]]
    )

    parsed = parse_pdf(str(pdf_path))

    assert len(parsed.pages) == 2
    assert "Bab satu isi" in parsed.pages[0]
    assert [t[1] for t in parsed.toc] == ["Bab Satu", "Bab Dua"]


def test_parse_pdf_empty_pages_raises_error(tmp_path):
    pdf_path = tmp_path / "kosong.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    with pytest.raises(PdfParsingError):
        parse_pdf(str(pdf_path))


def test_parse_pdf_corrupt_file_raises_error(tmp_path):
    bad_path = tmp_path / "rusak.pdf"
    bad_path.write_bytes(b"bukan file pdf yang valid")

    with pytest.raises(PdfParsingError):
        parse_pdf(str(bad_path))
