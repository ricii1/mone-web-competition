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


async def _fake_groq(redis, system_prompt, user_prompt, model_cls):
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
    pool.enqueue_job.assert_awaited_once_with("generate_levels_and_questions", class_id)
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
