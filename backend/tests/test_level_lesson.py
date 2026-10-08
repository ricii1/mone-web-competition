import uuid

import pytest
from pydantic import ValidationError

from app.core.security import create_access_token, hash_password
from app.models.class_ import Class, ClassStatus, ClassVisibility, Enrollment
from app.models.level import Level, LevelChunk, LevelType
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.progress import Progress, ProgressStatus
from app.models.question import Question, QuestionStatus
from app.models.user import User, UserRole
from app.schemas.generation import GeneratedLevelLesson, GeneratedLevelSummary


def _user(db, role: UserRole) -> User:
    user = User(
        name="x", email=f"{uuid.uuid4()}@x.com", password_hash=hash_password("pw"), role=role
    )
    db.add(user)
    db.commit()
    return user


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


def _setup(db, published: bool = True):
    teacher = _user(db, UserRole.teacher)
    cls = Class(
        teacher_id=teacher.id,
        title="Kelas",
        visibility=ClassVisibility.public,
        status=ClassStatus.published if published else ClassStatus.draft,
    )
    db.add(cls)
    db.commit()
    level = Level(
        class_id=cls.id,
        title="Level",
        type=LevelType.lesson_quiz,
        order_index=0,
        summary="Ringkasan",
        key_points=["Satu", "Dua", "Tiga"],
    )
    db.add(level)
    db.commit()
    return teacher, cls, level


def _question(db, level, status=QuestionStatus.approved, answer="B") -> Question:
    q = Question(
        level_id=level.id,
        question_text="Soal?",
        options=["A", "B", "C", "D"],
        correct_answer=answer,
        explanation="Karena B.",
        status=status,
    )
    db.add(q)
    db.commit()
    return q


def test_patch_summary_and_key_points(client, db):
    teacher, _, level = _setup(db)
    resp = client.patch(
        f"/api/v1/levels/{level.id}",
        json={"summary": "Baru", "key_points": ["  Poin A ", "Poin B"]},
        headers=_auth(teacher),
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Baru"
    assert resp.json()["key_points"] == ["Poin A", "Poin B"]


@pytest.mark.parametrize("points", [["ok", "   "], [""], [f"p{i}" for i in range(9)]])
def test_patch_invalid_key_points_rejected(client, db, points):
    teacher, _, level = _setup(db)
    resp = client.patch(
        f"/api/v1/levels/{level.id}", json={"key_points": points}, headers=_auth(teacher)
    )
    assert resp.status_code == 422


def test_other_teacher_cannot_patch(client, db):
    _, _, level = _setup(db)
    other = _user(db, UserRole.teacher)
    resp = client.patch(f"/api/v1/levels/{level.id}", json={"summary": "x"}, headers=_auth(other))
    assert resp.status_code == 403


def test_approve_level_requires_approved_question(client, db):
    teacher, _, level = _setup(db)
    _question(db, level, status=QuestionStatus.draft)
    resp = client.patch(
        f"/api/v1/levels/{level.id}", json={"status": "approved"}, headers=_auth(teacher)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Level belum punya soal approved"

    _question(db, level)
    resp = client.patch(
        f"/api/v1/levels/{level.id}", json={"status": "approved"}, headers=_auth(teacher)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_unapprove_always_allowed(client, db):
    teacher, _, level = _setup(db)
    level.status = "approved"
    db.commit()
    resp = client.patch(
        f"/api/v1/levels/{level.id}", json={"status": "draft"}, headers=_auth(teacher)
    )
    assert resp.status_code == 200


def test_levels_list_includes_key_points_and_ordered_sources(client, db):
    teacher, cls, level = _setup(db)
    material = Material(
        class_id=cls.id, file_name="a.pdf", file_path="/a", vector_status=VectorStatus.ready
    )
    db.add(material)
    db.commit()
    for title, start, end in [("Bab 2", 5, 7), ("Bab 1", 1, 4)]:
        chunk = MaterialChunk(
            material_id=material.id,
            class_id=cls.id,
            section_title=title,
            content="isi",
            page_start=start,
            page_end=end,
            embedding=[0.1] * 384,
        )
        db.add(chunk)
        db.commit()
        db.add(LevelChunk(level_id=level.id, chunk_id=chunk.id))
    db.commit()

    resp = client.get(f"/api/v1/classes/{cls.id}/levels", headers=_auth(teacher))
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["key_points"] == ["Satu", "Dua", "Tiga"]
    assert item["sources"] == [
        {"section_title": "Bab 1", "page_start": 1, "page_end": 4},
        {"section_title": "Bab 2", "page_start": 5, "page_end": 7},
    ]


def test_levels_list_sources_empty_without_chunks(client, db):
    teacher, cls, _ = _setup(db)
    resp = client.get(f"/api/v1/classes/{cls.id}/levels", headers=_auth(teacher))
    assert resp.json()[0]["sources"] == []


def _enroll(db, cls, level):
    student = _user(db, UserRole.student)
    db.add(Enrollment(user_id=student.id, class_id=cls.id))
    db.add(Progress(user_id=student.id, level_id=level.id, status=ProgressStatus.unlocked))
    db.commit()
    return student


def test_student_question_list_hides_correct_answer(client, db):
    _, cls, level = _setup(db)
    _question(db, level)
    _question(db, level, status=QuestionStatus.draft)
    student = _enroll(db, cls, level)
    resp = client.get(f"/api/v1/levels/{level.id}/questions", headers=_auth(student))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert "correct_answer" not in body[0]


def test_submit_returns_per_question_results(client, db):
    _, cls, level = _setup(db)
    right = _question(db, level)
    wrong = _question(db, level)
    skipped = _question(db, level)
    student = _enroll(db, cls, level)
    resp = client.post(
        f"/api/v1/levels/{level.id}/submit",
        json={"answers": {str(right.id): "B", str(wrong.id): "A"}},
        headers=_auth(student),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct_count"] == 1 and data["total_count"] == 3
    by_id = {r["question_id"]: r for r in data["results"]}
    assert by_id[str(right.id)] == {
        "question_id": str(right.id),
        "your_answer": "B",
        "is_correct": True,
        "correct_answer": "B",
        "explanation": "Karena B.",
    }
    assert by_id[str(wrong.id)]["is_correct"] is False
    assert by_id[str(wrong.id)]["your_answer"] == "A"
    assert by_id[str(wrong.id)]["correct_answer"] == "B"
    assert by_id[str(skipped.id)]["your_answer"] is None


def test_generated_summary_validation():
    with pytest.raises(ValidationError):
        GeneratedLevelSummary(summary="x", key_points=["a", "b"])
    with pytest.raises(ValidationError):
        GeneratedLevelSummary(summary="x", key_points=["a"] * 7)
    with pytest.raises(ValidationError):
        GeneratedLevelSummary(summary="x", key_points=["a", "b", " "])
    with pytest.raises(ValidationError):
        GeneratedLevelSummary(summary="", key_points=["a", "b", "c"])


def test_generated_lesson_validation():
    ok = "Isi materi yang cukup panjang. " * 10
    GeneratedLevelLesson(content=ok, summary="x", key_points=["a", "b", "c"])
    with pytest.raises(ValidationError):
        GeneratedLevelLesson(content="terlalu pendek", summary="x", key_points=["a", "b", "c"])
    with pytest.raises(ValidationError):
        GeneratedLevelLesson(content=" " * 300, summary="x", key_points=["a", "b", "c"])
    with pytest.raises(ValidationError):
        GeneratedLevelLesson(content=ok, summary="", key_points=["a", "b", "c"])
    with pytest.raises(ValidationError):
        GeneratedLevelLesson(content=ok, summary="x", key_points=["a", "b"])


def test_patch_content_strips_and_empty_clears(client, db):
    teacher, cls, level = _setup(db)
    resp = client.patch(
        f"/api/v1/levels/{level.id}",
        json={"content": "  ### Judul\n\nIsi.  "},
        headers=_auth(teacher),
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "### Judul\n\nIsi."
    listed = client.get(f"/api/v1/classes/{cls.id}/levels", headers=_auth(teacher)).json()
    assert listed[0]["content"] == "### Judul\n\nIsi."

    resp = client.patch(f"/api/v1/levels/{level.id}", json={"content": ""}, headers=_auth(teacher))
    assert resp.status_code == 200
    assert resp.json()["content"] is None


def test_patch_content_too_long_rejected(client, db):
    teacher, _, level = _setup(db)
    resp = client.patch(
        f"/api/v1/levels/{level.id}", json={"content": "a" * 20001}, headers=_auth(teacher)
    )
    assert resp.status_code == 422


def test_student_sees_content_of_enrolled_published_class(client, db):
    teacher, cls, level = _setup(db)
    level.content = "### Materi\n\nIsi bacaan."
    student = _user(db, UserRole.student)
    db.add(Enrollment(user_id=student.id, class_id=cls.id))
    db.commit()
    resp = client.get(f"/api/v1/classes/{cls.id}/levels", headers=_auth(student))
    assert resp.status_code == 200
    assert resp.json()[0]["content"] == "### Materi\n\nIsi bacaan."
