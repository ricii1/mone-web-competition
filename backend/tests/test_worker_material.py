import uuid

from app.models.class_ import Class, ClassVisibility
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.user import User, UserRole
from app.rag.chunking import Chunk
from app.rag.parsing import ParsedPdf, PdfParsingError
from app.worker.jobs import material as material_job


def _setup(db):
    teacher = User(
        name="t", email=f"{uuid.uuid4()}@x.com", password_hash="h", role=UserRole.teacher
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    cls = Class(teacher_id=teacher.id, title="K", visibility=ClassVisibility.public)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    mat = Material(class_id=cls.id, file_name="a.pdf", file_path="/tmp/a.pdf")
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return mat


async def test_process_material_success_sets_ready(db, monkeypatch):
    mat = _setup(db)

    monkeypatch.setattr(
        material_job, "parse_pdf", lambda path: ParsedPdf(pages=["a"], toc=[], headings=[])
    )
    monkeypatch.setattr(
        material_job,
        "chunk_parsed_pdf",
        lambda parsed: [Chunk(section_title=None, content="isi", page_start=0, page_end=0)],
    )
    monkeypatch.setattr(material_job, "embed_passages", lambda texts: [[0.1] * 384 for _ in texts])

    await material_job.process_material({}, str(mat.id))

    db.refresh(mat)
    assert mat.vector_status == VectorStatus.ready
    chunks = db.query(MaterialChunk).filter_by(material_id=mat.id).all()
    assert len(chunks) == 1


async def test_process_material_parsing_failure_sets_failed(db, monkeypatch):
    mat = _setup(db)

    def raise_error(path):
        raise PdfParsingError("rusak")

    monkeypatch.setattr(material_job, "parse_pdf", raise_error)

    await material_job.process_material({}, str(mat.id))

    db.refresh(mat)
    assert mat.vector_status == VectorStatus.failed
    assert mat.error_message


async def test_process_material_is_idempotent_on_rerun(db, monkeypatch):
    mat = _setup(db)
    monkeypatch.setattr(
        material_job, "parse_pdf", lambda path: ParsedPdf(pages=["a"], toc=[], headings=[])
    )
    monkeypatch.setattr(
        material_job,
        "chunk_parsed_pdf",
        lambda parsed: [Chunk(section_title=None, content="isi", page_start=0, page_end=0)],
    )
    monkeypatch.setattr(material_job, "embed_passages", lambda texts: [[0.1] * 384 for _ in texts])

    await material_job.process_material({}, str(mat.id))
    await material_job.process_material({}, str(mat.id))

    chunks = db.query(MaterialChunk).filter_by(material_id=mat.id).all()
    assert len(chunks) == 1
