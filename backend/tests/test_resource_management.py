import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.models.class_ import Class, ClassVisibility, Enrollment, GenerationStatus
from app.models.level import Level, LevelChunk, LevelType
from app.models.live_session import LiveParticipant, LiveSession, LiveSessionStatus
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.progress import Attempt, Progress, ProgressStatus
from app.models.question import Question
from app.models.user import User, UserRole
from app.rag.chunking import Chunk
from app.rag.parsing import ParsedPdf
from app.schemas.generation import GeneratedQuestion, GeneratedQuestionsOutput
from app.schemas.question import QuestionCreateRequest, QuestionUpdateRequest
from app.services import question_service, resource_deletion
from app.worker.jobs import material as job
from tests.test_live_session import _setup, _user
from tests.test_material_pdf import _headers


@pytest.fixture
def resources(db, tmp_path, monkeypatch):
    teacher, student, live, question = _setup(db)
    cls = db.get(Class, live.class_id)
    live.status = LiveSessionStatus.finished
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    directory = tmp_path / str(cls.id)
    directory.mkdir()
    path = directory / "original.pdf"
    path.write_bytes(b"%PDF-1.4 source")
    material = Material(
        class_id=cls.id,
        file_name="Sumber.pdf",
        file_path=str(path),
        vector_status=VectorStatus.failed,
    )
    db.add(material)
    db.commit()
    return cls, teacher, student, live, question, material, path


def _chunk(db, material, order=0, content="Sumber tumbuhan."):
    chunk = MaterialChunk(
        material_id=material.id,
        class_id=material.class_id,
        section_title=f"Bab {order}",
        content=content,
        order_index=order,
        page_start=0,
        page_end=1,
        embedding=[0.1] * 384,
    )
    db.add(chunk)
    db.commit()
    return chunk


def _base(cls, material):
    return f"/api/v1/classes/{cls.id}/materials/{material.id}"


def test_preview_paginates_in_source_order_without_embedding_or_full_text(client, db, resources):
    cls, teacher, student, _, _, material, _ = resources
    material.vector_status = VectorStatus.ready
    db.commit()
    last = _chunk(db, material, 2, "x" * 500)
    first = _chunk(db, material, 0)
    _chunk(db, material, 1)
    url = _base(cls, material) + "/sections"
    response = client.get(url + "?limit=2", headers=_headers(teacher))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert [s["order_index"] for s in data["sections"]] == [0, 1]
    assert data["sections"][0]["id"] == str(first.id)
    assert "embedding" not in data["sections"][0] and "content" not in data["sections"][0]
    tail = client.get(url + "?offset=2&limit=2", headers=_headers(teacher)).json()
    assert tail["sections"][0]["character_count"] == 500
    assert len(tail["sections"][0]["excerpt"]) == 400
    full = client.get(url + f"/{last.id}", headers=_headers(teacher))
    assert full.json() == {"id": str(last.id), "content": "x" * 500}
    assert client.get(url, headers=_headers(student)).status_code == 403
    assert client.get(url + "?limit=51", headers=_headers(teacher)).status_code == 422
    assert client.get(url + f"/{uuid.uuid4()}", headers=_headers(teacher)).status_code == 404


def test_preview_rejects_not_ready_and_cross_class(client, db, resources):
    cls, teacher, _, _, _, material, _ = resources
    assert (
        client.get(_base(cls, material) + "/sections", headers=_headers(teacher)).status_code == 409
    )
    other = Class(teacher_id=teacher.id, title="Lain", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    assert (
        client.get(
            f"/api/v1/classes/{other.id}/materials/{material.id}/sections",
            headers=_headers(teacher),
        ).status_code
        == 404
    )


def test_retry_enqueues_once_with_new_identity_and_clears_error(client, db, resources, monkeypatch):
    cls, teacher, _, _, _, material, path = resources
    material.error_message = "rusak"
    db.commit()
    pool = AsyncMock()
    monkeypatch.setattr("app.worker.queue.get_arq_pool", AsyncMock(return_value=pool))
    response = client.post(_base(cls, material) + "/retry", headers=_headers(teacher))
    assert response.status_code == 200
    db.refresh(material)
    assert material.vector_status == VectorStatus.pending and material.error_message is None
    assert path.exists()
    pool.enqueue_job.assert_awaited_once_with(
        "process_material",
        str(material.id),
        material.processing_job_id,
        _job_id=material.processing_job_id,
    )
    assert (
        client.post(_base(cls, material) + "/retry", headers=_headers(teacher)).status_code == 409
    )
    assert pool.enqueue_job.await_count == 1


def test_retry_enqueue_failure_remains_retryable(client, db, resources, monkeypatch):
    cls, teacher, _, _, _, material, path = resources
    monkeypatch.setattr("app.worker.queue.get_arq_pool", AsyncMock(side_effect=ConnectionError()))
    assert (
        client.post(_base(cls, material) + "/retry", headers=_headers(teacher)).status_code == 503
    )
    db.refresh(material)
    assert material.vector_status == VectorStatus.failed and material.error_message
    assert path.exists()


@pytest.mark.parametrize("operation", ["retry", "delete"])
def test_failed_material_actions_require_owner_and_unreferenced_source(
    client, db, resources, operation
):
    cls, teacher, student, _, question, material, path = resources
    url = _base(cls, material) + ("/retry" if operation == "retry" else "")
    call = client.post if operation == "retry" else client.delete
    assert call(url, headers=_headers(student)).status_code == 403
    outsider = _user(db, UserRole.teacher)
    assert call(url, headers=_headers(outsider)).status_code == 403
    chunk = _chunk(db, material)
    question.source_chunk_id = chunk.id
    db.commit()
    assert call(url, headers=_headers(teacher)).status_code == 409
    question.source_chunk_id = None
    db.add(LevelChunk(level_id=question.level_id, chunk_id=chunk.id))
    db.commit()
    assert call(url, headers=_headers(teacher)).status_code == 409
    assert path.exists()


def test_delete_failed_material_removes_file_and_chunks_only(client, db, resources):
    cls, teacher, _, _, question, material, path = resources
    _chunk(db, material)
    assert client.delete(_base(cls, material), headers=_headers(teacher)).status_code == 204
    assert not path.exists()
    assert db.query(Material).count() == db.query(MaterialChunk).count() == 0
    assert db.get(Question, question.id) is not None


async def test_material_delete_restores_file_when_transaction_fails(db, resources, monkeypatch):
    cls, teacher, _, _, _, material, path = resources
    monkeypatch.setattr(
        db, "commit", lambda: (_ for _ in ()).throw(RuntimeError("database unavailable"))
    )
    with pytest.raises(RuntimeError):
        await resource_deletion.delete_failed_material(db, cls.id, material.id, teacher)
    assert path.read_bytes() == b"%PDF-1.4 source"
    assert db.get(Material, material.id) is not None


async def test_stale_or_duplicate_material_job_cannot_reprocess(db, resources, monkeypatch):
    _, _, _, _, _, material, _ = resources
    material.processing_job_id = "new"
    material.vector_status = VectorStatus.pending
    db.commit()
    calls = []
    monkeypatch.setattr(
        job,
        "parse_pdf",
        lambda path: calls.append(path) or ParsedPdf(pages=["ok"], toc=[], headings=[]),
    )
    monkeypatch.setattr(
        job,
        "chunk_parsed_pdf",
        lambda parsed: [Chunk(section_title="Sumber", content="isi", page_start=0, page_end=0)],
    )
    monkeypatch.setattr(job, "embed_passages", lambda texts: [[0.1] * 384 for _ in texts])
    await job.process_material({}, str(material.id), "old")
    await job.process_material({}, str(material.id))
    assert not calls
    await job.process_material({}, str(material.id), "new")
    await job.process_material({}, str(material.id), "new")
    assert len(calls) == 1
    db.refresh(material)
    assert material.vector_status == VectorStatus.ready


async def test_cancelled_material_job_is_failed_and_retryable(db, resources, monkeypatch):
    _, _, _, _, _, material, _ = resources
    material.processing_job_id = "current"
    material.vector_status = VectorStatus.pending
    db.commit()
    monkeypatch.setattr(job.asyncio, "to_thread", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await job.process_material({}, str(material.id), "current")
    db.refresh(material)
    assert material.vector_status == VectorStatus.failed


def _delete(client, cls, teacher, title=None):
    return client.request(
        "DELETE",
        f"/api/v1/classes/{cls.id}",
        headers=_headers(teacher),
        json={"confirm_title": cls.title if title is None else title},
    )


async def test_delete_class_removes_entire_graph_files_and_cache_preserves_users(
    db, resources, _fake_redis
):
    cls, teacher, student, live, question, material, path = resources
    chunk = _chunk(db, material)
    question.source_chunk_id = chunk.id
    db.add(LevelChunk(level_id=question.level_id, chunk_id=chunk.id))
    db.add(Enrollment(class_id=cls.id, user_id=student.id))
    db.add(
        Progress(
            user_id=student.id,
            level_id=question.level_id,
            status=ProgressStatus.completed,
            best_score=100,
        )
    )
    db.add(
        Attempt(
            user_id=student.id,
            question_id=question.id,
            user_answer="4",
            is_correct=True,
            live_session_id=live.id,
        )
    )
    db.add(
        Level(
            class_id=cls.id,
            title="Ekor",
            type=LevelType.lesson_quiz,
            order_index=1,
            prerequisite_id=question.level_id,
        )
    )
    other = Class(teacher_id=teacher.id, title="Tetap ada", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    cls_id, live_id = cls.id, live.id
    await _fake_redis.set(f"leaderboard:{cls_id}", "cache")
    await _fake_redis.set(f"live:{live_id}:question", "cache")
    await resource_deletion.delete_class(db, cls_id, teacher, cls.title)
    db.expire_all()
    assert db.get(Class, cls_id) is None
    assert db.get(Class, other.id) is not None
    assert db.query(User).count() == 2
    for model in (
        Material,
        MaterialChunk,
        Level,
        LevelChunk,
        Question,
        Enrollment,
        Progress,
        Attempt,
        LiveSession,
        LiveParticipant,
    ):
        assert db.query(model).count() == 0
    assert not path.parent.exists()
    assert await _fake_redis.get(f"leaderboard:{cls_id}") is None
    assert await _fake_redis.get(f"live:{live_id}:question") is None


def test_class_delete_requires_owner_exact_title_and_finished_jobs(client, db, resources):
    cls, teacher, student, live, _, material, path = resources
    assert _delete(client, cls, student).status_code == 403
    assert _delete(client, cls, teacher, "wrong").status_code == 400
    cls.generation_status = GenerationStatus.generating
    db.commit()
    assert _delete(client, cls, teacher).status_code == 409
    cls.generation_status = GenerationStatus.idle
    for state in (VectorStatus.pending, VectorStatus.processing):
        material.vector_status = state
        db.commit()
        assert _delete(client, cls, teacher).status_code == 409
    material.vector_status = VectorStatus.failed
    for state in (LiveSessionStatus.waiting, LiveSessionStatus.running):
        live.status = state
        db.commit()
        assert _delete(client, cls, teacher).status_code == 409
    assert path.exists()


async def test_class_delete_restores_directory_and_all_rows_on_failure(db, resources, monkeypatch):
    cls, teacher, _, _, _, _, path = resources
    monkeypatch.setattr(
        db, "commit", lambda: (_ for _ in ()).throw(RuntimeError("database unavailable"))
    )
    with pytest.raises(RuntimeError):
        await resource_deletion.delete_class(db, cls.id, teacher, cls.title)
    assert path.read_bytes() == b"%PDF-1.4 source"
    assert db.query(Class).count() == db.query(Material).count() == db.query(Question).count() == 1


def test_class_delete_blocks_cross_class_prerequisite(client, db, resources):
    cls, teacher, _, _, question, _, path = resources
    other = Class(teacher_id=teacher.id, title="Lain", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    db.add(
        Level(
            class_id=other.id,
            title="Lain",
            type=LevelType.lesson_quiz,
            order_index=0,
            prerequisite_id=question.level_id,
        )
    )
    db.commit()
    assert _delete(client, cls, teacher).status_code == 409
    assert path.exists()


@pytest.mark.parametrize("operation", ["class", "material"])
def test_deletion_rejects_symlink_escape(client, resources, tmp_path, operation):
    cls, teacher, _, _, _, material, path = resources
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-outside")
    path.unlink()
    if operation == "material":
        path.symlink_to(outside)
        response = client.delete(_base(cls, material), headers=_headers(teacher))
    else:
        path.parent.rmdir()
        external = tmp_path / "external"
        external.mkdir()
        (external / "safe.pdf").write_bytes(b"%PDF-safe")
        path.parent.symlink_to(external, target_is_directory=True)
        response = _delete(client, cls, teacher)
    assert response.status_code == 409
    assert outside.read_bytes() == b"%PDF-outside"


def _generated(text):
    return GeneratedQuestion(
        question_text=text,
        options=["a", "b", "c", "d"],
        correct_answer="a",
        explanation="Dari sumber",
    )


def test_generated_questions_reject_normalized_duplicates_and_blank():
    with pytest.raises(ValidationError):
        GeneratedQuestionsOutput(
            questions=[_generated("Apa   fungsi daun?"), _generated("  APA fungsi\nDAUN? ")]
        )
    with pytest.raises(ValidationError):
        GeneratedQuestionsOutput(questions=[_generated("   ")])
    assert (
        len(
            GeneratedQuestionsOutput(
                questions=[_generated("Apa fungsi daun?"), _generated("Apa fungsi akar?")]
            ).questions
        )
        == 2
    )


def test_manual_create_and_edit_reject_duplicates_preserve_original(db, resources):
    _, _, _, _, question, _, _ = resources
    body = QuestionCreateRequest(
        question_text="  2+2?  ", options=["3", "4", "5", "6"], correct_answer="4"
    )
    with pytest.raises(HTTPException) as exc:
        question_service.create_question(db, question.level_id, body)
    assert exc.value.status_code == 409
    db.rollback()
    body.question_text = "Apa fungsi akar?"
    other = question_service.create_question(db, question.level_id, body)
    with pytest.raises(HTTPException):
        question_service.update_question(db, other, QuestionUpdateRequest(question_text="2+2?"))
    db.rollback()
    db.refresh(other)
    assert other.question_text == "Apa fungsi akar?"
    assert db.query(Question).count() == 2
    question_service.update_question(
        db, other, QuestionUpdateRequest(question_text="  APA fungsi akar? ")
    )


def test_class_delete_endpoint_cleans_class_and_returns_204(client, db, resources):
    cls, teacher, _, _, _, _, path = resources
    class_id = cls.id
    assert _delete(client, cls, teacher).status_code == 204
    db.expire_all()
    assert db.get(Class, class_id) is None
    assert not path.parent.exists()
    assert client.get(f"/api/v1/classes/{class_id}", headers=_headers(teacher)).status_code == 404


async def test_duplicate_generated_questions_trigger_bounded_llm_retry(monkeypatch, _fake_redis):
    import json

    from app.rag import llm

    repeated = {
        "questions": [
            _generated("Apa fungsi daun?").model_dump(),
            _generated("  APA fungsi daun? ").model_dump(),
        ]
    }
    valid = {
        "questions": [
            _generated("Apa fungsi daun?").model_dump(),
            _generated("Apa fungsi akar?").model_dump(),
        ]
    }
    outputs = iter([json.dumps(repeated), json.dumps(valid)])
    call = AsyncMock(side_effect=lambda *args: next(outputs))
    monkeypatch.setattr(llm, "call_groq_with_backoff", call)
    result = await llm.call_groq_structured(_fake_redis, "system", "user", GeneratedQuestionsOutput)
    assert len(result.questions) == 2
    assert call.await_count == 2
    call = AsyncMock(return_value=json.dumps(repeated))
    monkeypatch.setattr(llm, "call_groq_with_backoff", call)
    with pytest.raises(llm.LlmOutputError):
        await llm.call_groq_structured(_fake_redis, "system", "user", GeneratedQuestionsOutput)
    assert call.await_count == llm.MAX_JSON_RETRIES + 1


async def test_notification_failure_does_not_revert_ready_material(db, resources, monkeypatch):
    _, _, _, _, _, material, _ = resources
    monkeypatch.setattr(job, "publish_event", AsyncMock(side_effect=ConnectionError("pubsub down")))
    monkeypatch.setattr(job, "parse_pdf", lambda path: ParsedPdf(pages=["ok"], toc=[], headings=[]))
    monkeypatch.setattr(
        job,
        "chunk_parsed_pdf",
        lambda parsed: [Chunk(section_title="Sumber", content="isi", page_start=0, page_end=0)],
    )
    monkeypatch.setattr(job, "embed_passages", lambda texts: [[0.1] * 384 for _ in texts])
    await job.process_material({}, str(material.id))
    db.refresh(material)
    assert material.vector_status == VectorStatus.ready
    assert db.query(MaterialChunk).count() == 1


@pytest.mark.parametrize("operation", ["retry", "delete"])
def test_material_actions_reject_active_generation_and_missing_files(
    client, db, resources, operation
):
    cls, teacher, _, _, _, material, path = resources
    call = client.post if operation == "retry" else client.delete
    url = _base(cls, material) + ("/retry" if operation == "retry" else "")
    cls.generation_status = GenerationStatus.generating
    db.commit()
    assert call(url, headers=_headers(teacher)).status_code == 409
    cls.generation_status = GenerationStatus.idle
    material.vector_status = VectorStatus.processing
    db.commit()
    assert call(url, headers=_headers(teacher)).status_code == 409
    material.vector_status = VectorStatus.failed
    db.commit()
    path.unlink()
    assert call(url, headers=_headers(teacher)).status_code == (
        404 if operation == "retry" else 204
    )


async def test_legacy_ready_job_preserves_source_already_used_by_level(db, resources, monkeypatch):
    _, _, _, _, question, material, _ = resources
    chunk = _chunk(db, material)
    material.vector_status = VectorStatus.ready
    db.add(LevelChunk(level_id=question.level_id, chunk_id=chunk.id))
    db.commit()
    parser = AsyncMock(side_effect=AssertionError("Referenced source must not be replaced"))
    monkeypatch.setattr(job, "parse_pdf", parser)
    await job.process_material({}, str(material.id))
    db.refresh(material)
    assert material.vector_status == VectorStatus.ready
    assert db.query(LevelChunk).one().chunk_id == chunk.id
    assert db.query(MaterialChunk).one().content == "Sumber tumbuhan."
    parser.assert_not_called()
