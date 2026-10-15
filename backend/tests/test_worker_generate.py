import uuid
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.models.class_ import Class, ClassVisibility, GenerationStatus
from app.models.level import Level, LevelChunk, LevelStatus, LevelType
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.question import Question, QuestionStatus
from app.models.user import User, UserRole
from app.schemas.generation import (
    GeneratedLevelLesson,
    GeneratedLevelSummary,
    GeneratedQuestion,
    GeneratedQuestionsOutput,
)
from app.services.level_service import LEVELS_PER_BOSS
from app.worker.jobs import generate_content as job


def _setup(db, n_chunks=5, is_example=False):
    teacher = User(
        name="t", email=f"{uuid.uuid4()}@x.com", password_hash="h", role=UserRole.teacher
    )
    db.add(teacher)
    db.commit()
    cls = Class(
        teacher_id=teacher.id, title="K", visibility=ClassVisibility.public, is_example=is_example
    )
    db.add(cls)
    db.commit()
    mat = Material(
        class_id=cls.id, file_name="a.pdf", file_path="/tmp/a.pdf", vector_status=VectorStatus.ready
    )
    db.add(mat)
    db.commit()
    for i in range(n_chunks):
        db.add(
            MaterialChunk(
                material_id=mat.id,
                class_id=cls.id,
                section_title=f"Bab {i + 1}",
                content=f"isi {i}",
                order_index=i,
                page_start=i,
                page_end=i,
                embedding=[0.1] * 384,
            )
        )
    db.commit()
    return cls


def _fake_question(i: int) -> GeneratedQuestion:
    return GeneratedQuestion(
        question_text=f"Soal {i}?",
        options=["A", "B", "C", "D"],
        correct_answer="B",
        explanation="Karena B.",
    )


FAKE_CONTENT = "### Judul\n\n" + "Ini adalah isi materi yang cukup panjang untuk murid. " * 6


async def _fake_groq(redis, system_prompt, user_prompt, model_cls):
    if model_cls is GeneratedLevelLesson:
        return GeneratedLevelLesson(
            content=FAKE_CONTENT, summary="ringkasan", key_points=["a", "b", "c"]
        )
    if model_cls is GeneratedLevelSummary:
        return GeneratedLevelSummary(summary="ringkasan", key_points=["a", "b", "c"])
    return GeneratedQuestionsOutput(questions=[_fake_question(i) for i in range(5)])


@pytest.fixture
def events(monkeypatch):
    captured = []

    async def fake_publish(channel, event):
        captured.append(event)

    monkeypatch.setattr(job, "publish_event", fake_publish)
    monkeypatch.setattr(job, "call_groq_structured", _fake_groq)
    return captured


async def test_success_creates_levels_with_boss_and_chain(db, events):
    cls = _setup(db, n_chunks=5)

    await job.generate_levels_and_questions({}, str(cls.id))

    levels = db.query(Level).filter_by(class_id=cls.id).order_by(Level.order_index).all()
    # 5 lessons + 1 boss after the 4th lesson (not after the last one)
    assert [lv.type for lv in levels] == [LevelType.lesson_quiz] * LEVELS_PER_BOSS + [
        LevelType.boss,
        LevelType.lesson_quiz,
    ]
    assert levels[0].prerequisite_id is None
    for prev, cur in zip(levels, levels[1:], strict=False):
        assert cur.prerequisite_id == prev.id
    assert all(lv.status == LevelStatus.draft for lv in levels)
    assert all(lv.key_points == ["a", "b", "c"] for lv in levels)
    # Lessons get the article; boss levels have summary + key points only.
    for lv in levels:
        if lv.type == LevelType.lesson_quiz:
            assert lv.content == FAKE_CONTENT.strip()
        else:
            assert lv.content is None
    for lv in levels:
        questions = db.query(Question).filter_by(level_id=lv.id).all()
        assert len(questions) == 5
        assert all(q.status == QuestionStatus.draft and len(q.options) == 4 for q in questions)
    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.done
    assert cls.generation_error is None
    types = [e.type for e in events]
    assert types.count("level_created") == 6
    assert events[-1].type == "generation_progress"
    assert events[-1].payload["stage"] == "done"


async def test_failure_sets_failed_with_error_and_event(db, events, monkeypatch):
    cls = _setup(db, n_chunks=2)
    monkeypatch.setattr(
        job, "call_groq_structured", AsyncMock(side_effect=RuntimeError("groq down"))
    )

    with pytest.raises(RuntimeError):
        await job.generate_levels_and_questions({}, str(cls.id))

    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.failed
    assert "groq down" in cls.generation_error
    assert events[-1].type == "generation_progress"
    assert events[-1].payload["stage"] == "failed"
    assert "groq down" in events[-1].payload["error_message"]


async def test_rerun_after_failure_replaces_drafts(db, events, monkeypatch):
    cls = _setup(db, n_chunks=3)
    calls = {"n": 0}

    async def flaky(redis, system_prompt, user_prompt, model_cls):
        calls["n"] += 1
        if calls["n"] > 3:
            raise RuntimeError("putus di tengah")
        return await _fake_groq(redis, system_prompt, user_prompt, model_cls)

    monkeypatch.setattr(job, "call_groq_structured", flaky)
    with pytest.raises(RuntimeError):
        await job.generate_levels_and_questions({}, str(cls.id))
    db.expire_all()
    assert db.query(Level).filter_by(class_id=cls.id).count() > 0

    monkeypatch.setattr(job, "call_groq_structured", _fake_groq)
    await job.generate_levels_and_questions({}, str(cls.id))
    await job.generate_levels_and_questions({}, str(cls.id))

    db.expire_all()
    levels = db.query(Level).filter_by(class_id=cls.id).all()
    assert len(levels) == 3
    assert db.query(LevelChunk).count() == 3
    assert db.query(Question).count() == 15
    assert db.get(Class, cls.id).generation_status == GenerationStatus.done


async def test_refuses_when_approved_level_exists(db, events):
    cls = _setup(db, n_chunks=2)
    db.add(
        Level(
            class_id=cls.id,
            title="Disetujui",
            type=LevelType.lesson_quiz,
            order_index=0,
            status=LevelStatus.approved,
        )
    )
    db.commit()

    with pytest.raises(ValueError):
        await job.generate_levels_and_questions({}, str(cls.id))

    db.expire_all()
    levels = db.query(Level).filter_by(class_id=cls.id).all()
    assert len(levels) == 1 and levels[0].status == LevelStatus.approved
    assert db.get(Class, cls.id).generation_status == GenerationStatus.failed


def test_schema_rejects_answer_not_in_options():
    with pytest.raises(ValidationError):
        GeneratedQuestion(
            question_text="?", options=["A", "B", "C", "D"], correct_answer="E", explanation="x"
        )


def test_schema_rejects_empty_questions():
    with pytest.raises(ValidationError):
        GeneratedQuestionsOutput(questions=[])


# --- route tests ---


def _register(client, email, role="teacher"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "secret123", "role": role},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_class(client, headers):
    resp = client.post(
        "/api/v1/classes", json={"title": "K", "visibility": "public"}, headers=headers
    )
    return resp.json()["id"]


@pytest.fixture
def pool(monkeypatch):
    fake = AsyncMock()
    monkeypatch.setattr("app.api.routes.levels.get_arq_pool", AsyncMock(return_value=fake))
    return fake


def _add_ready_material(db, class_id):
    db.add(
        Material(
            class_id=uuid.UUID(class_id),
            file_name="a.pdf",
            file_path="/tmp/a.pdf",
            vector_status=VectorStatus.ready,
        )
    )
    db.commit()


def test_route_accepts_and_marks_generating(client, db, pool):
    headers = _register(client, "r1@x.com")
    class_id = _make_class(client, headers)
    _add_ready_material(db, class_id)

    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)

    assert resp.status_code == 202
    assert resp.json() == {"status": "queued"}
    job_id = db.get(Class, uuid.UUID(class_id)).generation_job_id
    pool.enqueue_job.assert_awaited_once_with(
        "generate_levels_and_questions", class_id, job_id, _job_id=job_id
    )
    db.expire_all()
    assert db.get(Class, uuid.UUID(class_id)).generation_status == GenerationStatus.generating
    got = client.get(f"/api/v1/classes/{class_id}", headers=headers).json()
    assert got["generation_status"] == "generating"
    assert got["generation_error"] is None


def test_route_400_without_ready_material(client, pool):
    headers = _register(client, "r2@x.com")
    class_id = _make_class(client, headers)
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)
    assert resp.status_code == 400
    pool.enqueue_job.assert_not_awaited()


def test_route_409_when_already_generating(client, db, pool):
    headers = _register(client, "r3@x.com")
    class_id = _make_class(client, headers)
    _add_ready_material(db, class_id)
    assert (
        client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers).status_code
        == 202
    )
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)
    assert resp.status_code == 409


def test_route_409_when_approved_level_exists(client, db, pool):
    headers = _register(client, "r4@x.com")
    class_id = _make_class(client, headers)
    _add_ready_material(db, class_id)
    db.add(
        Level(
            class_id=uuid.UUID(class_id),
            title="L",
            type=LevelType.lesson_quiz,
            order_index=0,
            status=LevelStatus.approved,
        )
    )
    db.commit()
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)
    assert resp.status_code == 409


def test_route_non_owner_teacher_forbidden(client, db, pool):
    owner = _register(client, "r5@x.com")
    other = _register(client, "r6@x.com")
    class_id = _make_class(client, owner)
    _add_ready_material(db, class_id)
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=other)
    assert resp.status_code in (403, 404)
    resp = client.post(f"/api/v1/classes/{uuid.uuid4()}/levels/generate", headers=owner)
    assert resp.status_code == 404


def test_route_400_for_example_class(client, db, pool):
    headers = _register(client, "r7@x.com")
    class_id = _make_class(client, headers)
    _add_ready_material(db, class_id)
    cls = db.get(Class, uuid.UUID(class_id))
    cls.is_example = True
    db.commit()
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Class contoh tidak bisa digenerate"


def test_enqueue_failure_marks_failed_and_allows_retry(client, db, pool):
    headers = _register(client, "queuefail@x.com")
    class_id = _make_class(client, headers)
    _add_ready_material(db, class_id)
    pool.enqueue_job.side_effect = RuntimeError("Redis unavailable")
    response = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers)
    assert response.status_code == 503
    db.expire_all()
    assert db.get(Class, uuid.UUID(class_id)).generation_status == GenerationStatus.failed
    pool.enqueue_job.side_effect = None
    assert (
        client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=headers).status_code
        == 202
    )


async def test_cancelled_job_sets_failed(db, events, monkeypatch):
    import asyncio

    cls = _setup(db, n_chunks=1)
    monkeypatch.setattr(
        job, "call_groq_structured", AsyncMock(side_effect=asyncio.CancelledError())
    )
    with pytest.raises(asyncio.CancelledError):
        await job.generate_levels_and_questions({}, str(cls.id))
    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.failed
    assert cls.generation_error == "Waktu pemrosesan habis"


@pytest.mark.parametrize("failed_stage", ["generating_levels", "level_created", "done", "all"])
async def test_notification_failure_does_not_fail_generated_content(
    db, events, monkeypatch, failed_stage
):
    cls = _setup(db, n_chunks=5)

    async def failing_publish(channel, event):
        stage = event.payload.get("stage", event.type)
        if failed_stage in (stage, "all"):
            raise ConnectionError("Notification unavailable")

    monkeypatch.setattr(job, "publish_event", failing_publish)
    await job.generate_levels_and_questions({}, str(cls.id))
    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.done
    assert cls.generation_error is None
    levels = db.query(Level).filter_by(class_id=cls.id).all()
    assert len(levels) == 6
    assert db.query(Question).filter(Question.level_id.in_([lv.id for lv in levels])).count() == 30


async def test_notification_failure_preserves_original_generation_error(db, events, monkeypatch):
    cls = _setup(db, n_chunks=1)
    monkeypatch.setattr(job, "publish_event", AsyncMock(side_effect=ConnectionError("pubsub down")))
    monkeypatch.setattr(
        job, "call_groq_structured", AsyncMock(side_effect=ValueError("Bad source"))
    )
    with pytest.raises(ValueError, match="Bad source"):
        await job.generate_levels_and_questions({}, str(cls.id))
    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.failed
    assert cls.generation_error == "Bad source"


async def test_stale_worker_cannot_replace_new_generation(db, events):
    cls = _setup(db, n_chunks=1)
    cls.generation_job_id = "new-job"
    cls.generation_status = GenerationStatus.generating
    db.commit()
    await job.generate_levels_and_questions({}, str(cls.id), "old-job")
    assert db.query(Level).filter_by(class_id=cls.id).count() == 0
    db.refresh(cls)
    assert cls.generation_status == GenerationStatus.generating


@pytest.mark.parametrize(
    "job_status,recovered", [("not_found", True), ("queued", False), ("in_progress", False)]
)
async def test_recovery_preserves_queued_and_running_jobs(db, monkeypatch, job_status, recovered):
    from datetime import UTC, datetime, timedelta

    from arq.jobs import JobStatus

    from app.worker import recovery

    cls = _setup(db, n_chunks=1)
    cls.generation_status = GenerationStatus.generating
    cls.generation_job_id = "lost-job"
    cls.generation_requested_at = datetime.now(UTC) - timedelta(hours=2)
    db.commit()
    monkeypatch.setattr(recovery.Job, "status", AsyncMock(return_value=JobStatus(job_status)))
    await recovery.recover_generation(db, cls, AsyncMock())
    db.refresh(cls)
    assert (cls.generation_status == GenerationStatus.failed) == recovered


async def test_same_page_sections_follow_saved_order_not_insert_or_uuid_order(db, events):
    cls = _setup(db, n_chunks=0)
    mat = db.query(Material).filter_by(class_id=cls.id).one()
    for index in [2, 0, 1]:
        db.add(
            MaterialChunk(
                material_id=mat.id,
                class_id=cls.id,
                section_title=f"Subbab {index}",
                content=f"Isi bagian {index}",
                page_start=0,
                page_end=0,
                order_index=index,
                embedding=[0.1] * 384,
            )
        )
    db.commit()
    await job.generate_levels_and_questions({}, str(cls.id))
    levels = db.query(Level).filter_by(class_id=cls.id).order_by(Level.order_index).all()
    assert [level.title for level in levels] == ["Subbab 0", "Subbab 1", "Subbab 2"]
    assert [level.prerequisite_id for level in levels] == [None, levels[0].id, levels[1].id]


async def test_long_source_reaches_both_article_and_questions(db, monkeypatch):
    from app.rag import context as source_context
    from app.schemas.generation import GeneratedSourceNotes

    cls = _setup(db, n_chunks=0)
    material = db.query(Material).filter_by(class_id=cls.id).one()
    facts = [
        "Fakta awal: air bersih digunakan untuk mencuci tangan.",
        "Fakta tengah: akar tumbuhan menyerap air dari tanah.",
        "Fakta akhir: lampu belajar menggunakan energi listrik.",
    ]
    filler = "Tumbuhan perlu dirawat dengan menyiramnya secukupnya. " * 220
    source = facts[0] + filler + facts[1] + filler + facts[2]
    chunk = MaterialChunk(
        material_id=material.id,
        class_id=cls.id,
        section_title="Materi panjang",
        content=source,
        order_index=0,
        page_start=0,
        page_end=4,
        embedding=[0.1] * 384,
    )
    db.add(chunk)
    db.commit()
    seen_parts = []
    seen_article = []
    seen_questions = []

    def extract(prompt):
        return prompt.split("Konteks materi:\n", 1)[1].split("\n\nKembalikan HANYA JSON", 1)[0]

    async def notes(redis, system, prompt, schema):
        part = extract(prompt)
        seen_parts.append(part)
        selected = [fact for fact in facts if fact in part]
        return GeneratedSourceNotes(notes=" ".join(selected) or "Tumbuhan perlu dirawat.")

    async def generate(redis, system, prompt, schema):
        context = extract(prompt)
        if schema is GeneratedLevelLesson:
            seen_article.append(context)
            return GeneratedLevelLesson(
                content=FAKE_CONTENT + context, summary="Materi sumber", key_points=["a", "b", "c"]
            )
        seen_questions.append(context)
        return GeneratedQuestionsOutput(questions=[_fake_question(i) for i in range(5)])

    monkeypatch.setattr(source_context, "call_groq_structured", notes)
    monkeypatch.setattr(job, "call_groq_structured", generate)
    monkeypatch.setattr(job, "publish_event", AsyncMock())
    await job.generate_levels_and_questions({}, str(cls.id))
    assert "".join(seen_parts) == source
    assert seen_article == seen_questions
    assert all(fact in seen_article[0] for fact in facts)
    assert len(seen_article[0]) <= source_context.MAX_CONTEXT_CHARS
    levels = db.query(Level).filter_by(class_id=cls.id).all()
    assert len(levels) == 1
    assert facts[-1] in levels[0].content
    assert db.query(Question).filter_by(level_id=levels[0].id).count() == 5
