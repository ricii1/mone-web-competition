import pymupdf
import pytest

from app.rag.chunking import chunk_parsed_pdf
from app.rag.parsing import parse_pdf
from scripts.generate_pdf_layout_fixtures import MARKERS, SECTIONS, create_fixtures


@pytest.fixture
def layouts(tmp_path):
    return {path.stem: path for path in create_fixtures(tmp_path)}


@pytest.mark.parametrize(
    "name",
    [
        "one_section_per_page",
        "one_section_per_page_toc",
        "mixed_pages",
        "mixed_pages_toc",
    ],
)
def test_each_section_contains_only_its_source(layouts, name):
    chunks = chunk_parsed_pdf(parse_pdf(str(layouts[name])))
    assert [chunk.section_title for chunk in chunks] == list(SECTIONS)
    for index, chunk in enumerate(chunks):
        assert [marker for marker in MARKERS if marker in chunk.content] == [MARKERS[index]]
        if name.startswith("one_section"):
            body_words = chunk.content.split()[len(chunk.section_title.split()) :]
            assert body_words == SECTIONS[list(SECTIONS)[index]].split()
    expected_ranges = (
        [(0, 0), (1, 1), (2, 2)] if name.startswith("one_section") else [(0, 0), (0, 1), (1, 1)]
    )
    assert [(chunk.page_start, chunk.page_end) for chunk in chunks] == expected_ranges
    if name.startswith("mixed"):
        assert chunks[1].content.count("Akar tumbuhan") == 2


def test_bookmark_alias_uses_destination_position(tmp_path):
    path = tmp_path / "aliases.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((60, 72), "Judul pertama", fontsize=11)
        page.insert_text((60, 100), "Isi khusus pertama.", fontsize=11)
        page.insert_text((60, 300), "Judul kedua", fontsize=11)
        page.insert_text((60, 330), "Isi khusus kedua.", fontsize=11)
        doc.set_toc([[1, "Nama pertama", 1, 72], [1, "Nama kedua", 1, 300]])
        doc.save(path)
    chunks = chunk_parsed_pdf(parse_pdf(str(path)))
    assert [chunk.section_title for chunk in chunks] == ["Nama pertama", "Nama kedua"]
    assert "Isi khusus kedua" not in chunks[0].content
    assert "Isi khusus pertama" not in chunks[1].content
    assert "Isi khusus pertama" in chunks[0].content
    assert "Isi khusus kedua" in chunks[1].content


def test_heading_with_multiple_font_spans_is_one_boundary(tmp_path):
    path = tmp_path / "styled.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((60, 72), "Bagian", fontsize=18, fontname="hebo")
        page.insert_text((122, 72), "Tumbuhan", fontsize=18)
        page.insert_textbox((60, 100, 530, 250), SECTIONS["Bagian Tumbuhan"], fontsize=11)
        page.insert_text((60, 300), "Energi di Rumah", fontsize=18)
        page.insert_textbox((60, 325, 530, 750), SECTIONS["Energi di Rumah"], fontsize=11)
        doc.save(path)
    chunks = chunk_parsed_pdf(parse_pdf(str(path)))
    assert len(chunks) == 2
    assert "Bagian" in chunks[0].section_title and "Tumbuhan" in chunks[0].section_title
    assert "Lampu belajar" not in chunks[0].content
    assert "Akar tumbuhan" not in chunks[1].content


def test_unstructured_pdf_keeps_bounded_overlap(layouts):
    parsed = parse_pdf(str(layouts["unstructured_long"]))
    chunks = chunk_parsed_pdf(parsed)
    assert [len(chunk.content.split()) for chunk in chunks] == [500, 500, 105]
    assert chunks[0].content.split()[-50:] == chunks[1].content.split()[:50]
    assert chunks[1].content.split()[-50:] == chunks[2].content.split()[:50]


def test_heading_wrapped_over_two_lines_stays_one_section(tmp_path):
    path = tmp_path / "wrapped.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_textbox((60, 60, 250, 130), "Bagian Tumbuhan\ndi Sekitar Kita", fontsize=18)
        page.insert_textbox((60, 150, 530, 280), SECTIONS["Bagian Tumbuhan"], fontsize=11)
        page.insert_text((60, 340), "Energi di Rumah", fontsize=18)
        page.insert_textbox((60, 370, 530, 750), SECTIONS["Energi di Rumah"], fontsize=11)
        doc.save(path)
    chunks = chunk_parsed_pdf(parse_pdf(str(path)))
    assert [chunk.section_title for chunk in chunks] == [
        "Bagian Tumbuhan di Sekitar Kita",
        "Energi di Rumah",
    ]
    assert "Lampu belajar" not in chunks[0].content
    assert "Akar tumbuhan" not in chunks[1].content


def test_nested_bookmarks_with_same_start_do_not_duplicate_content(tmp_path):
    path = tmp_path / "nested.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((60, 72), "Air di Sekitar Kita", fontsize=11)
        page.insert_textbox((60, 100, 530, 270), SECTIONS["Air di Sekitar Kita"], fontsize=11)
        page.insert_text((60, 320), "Energi di Rumah", fontsize=11)
        page.insert_textbox((60, 350, 530, 750), SECTIONS["Energi di Rumah"], fontsize=11)
        doc.set_toc(
            [[1, "Bab", 1, 72], [2, "Air di Sekitar Kita", 1, 72], [2, "Energi di Rumah", 1, 320]]
        )
        doc.save(path)
    chunks = chunk_parsed_pdf(parse_pdf(str(path)))
    assert [chunk.section_title for chunk in chunks] == ["Air di Sekitar Kita", "Energi di Rumah"]
    assert "Lampu belajar" not in chunks[0].content
    assert "penampungan air" not in chunks[1].content


def test_introduction_and_continuation_are_not_lost(tmp_path):
    path = tmp_path / "intro.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((60, 72), "Pengantar untuk membaca materi ini.", fontsize=11)
        page.insert_text((60, 130), "Bagian Tumbuhan", fontsize=18)
        page.insert_textbox((60, 160, 530, 750), SECTIONS["Bagian Tumbuhan"], fontsize=11)
        page = doc.new_page()
        page.insert_text((60, 72), "Kelanjutan tumbuhan yang harus tetap tersimpan.", fontsize=11)
        page.insert_text((60, 130), "Energi di Rumah", fontsize=18)
        page.insert_textbox((60, 160, 530, 750), SECTIONS["Energi di Rumah"], fontsize=11)
        doc.save(path)
    chunks = chunk_parsed_pdf(parse_pdf(str(path)))
    assert len(chunks) == 2
    assert "Pengantar untuk membaca" in chunks[0].content
    assert "Kelanjutan tumbuhan" in chunks[0].content
    assert "Kelanjutan tumbuhan" not in chunks[1].content
    assert chunks[0].page_end == 1


@pytest.mark.parametrize("name", ["mixed_pages", "mixed_pages_toc"])
async def test_real_worker_keeps_level_and_question_sources_separate(
    db, layouts, monkeypatch, name
):
    from app.core.config import settings
    from app.models.class_ import Class, GenerationStatus
    from app.models.level import Level, LevelChunk
    from app.models.material import MaterialChunk, VectorStatus
    from app.models.question import Question
    from app.worker.jobs import generate_content
    from app.worker.jobs import material as material_job
    from tests.test_worker_material import _setup

    material = _setup(db)
    material.file_path = str(layouts[name])
    db.commit()
    monkeypatch.setattr(material_job, "embed_passages", lambda texts: [[0.1] * 384 for _ in texts])
    monkeypatch.setattr(settings, "llm_mode", "mock")
    monkeypatch.setattr(settings, "mock_llm_delay_seconds", 0)
    await material_job.process_material({}, str(material.id))
    await generate_content.generate_levels_and_questions({}, str(material.class_id))
    db.expire_all()
    assert material.vector_status == VectorStatus.ready
    assert db.get(Class, material.class_id).generation_status == GenerationStatus.done
    levels = db.query(Level).filter_by(class_id=material.class_id).order_by(Level.order_index).all()
    assert len(levels) == 3
    for index, level in enumerate(levels):
        assert [marker for marker in MARKERS if marker in level.content] == [MARKERS[index]]
        source_link = db.query(LevelChunk).filter_by(level_id=level.id).one()
        source = db.get(MaterialChunk, source_link.chunk_id)
        questions = db.query(Question).filter_by(level_id=level.id).all()
        assert len(questions) == 5
        assert source.section_title == level.title
        assert source.order_index == index
        assert [marker for marker in MARKERS if marker in source.content] == [MARKERS[index]]
        assert all(question.source_chunk_id == source.id for question in questions)
        for question in questions:
            for other_marker in MARKERS:
                if other_marker != MARKERS[index]:
                    assert other_marker not in question.explanation
