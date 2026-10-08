import uuid

from app.models.level import Level, LevelType
from app.models.question import Question, QuestionStatus
from app.services.example_class import EXAMPLE_TITLE


def _register(client, email, role):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "secret123", "role": role},
    )
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_owned_classes_includes_drafts_and_excludes_others(client):
    teacher_token = _register(client, "teacher_own@example.com", "teacher")
    other_token = _register(client, "teacher_other@example.com", "teacher")

    resp = client.post(
        "/api/v1/classes",
        json={"title": "Draft Class", "visibility": "public"},
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 201

    client.post(
        "/api/v1/classes",
        json={"title": "Other Teacher Class", "visibility": "public"},
        headers=_auth(other_token),
    )

    resp = client.get("/api/v1/classes/mine", headers=_auth(teacher_token))
    assert resp.status_code == 200
    titles = [c["title"] for c in resp.json()]
    # Every new teacher also gets the reference class; other teachers' classes stay hidden.
    assert sorted(titles) == sorted(["Draft Class", EXAMPLE_TITLE])


def test_student_cannot_list_owned_classes(client):
    student_token = _register(client, "student_own@example.com", "student")
    resp = client.get("/api/v1/classes/mine", headers=_auth(student_token))
    assert resp.status_code == 403


def test_new_teacher_gets_example_class_but_student_does_not(client):
    teacher_token = _register(client, "teacher_ex@example.com", "teacher")
    student_token = _register(client, "student_ex@example.com", "student")

    mine = client.get("/api/v1/classes/mine", headers=_auth(teacher_token)).json()
    assert [c["title"] for c in mine] == [EXAMPLE_TITLE]
    assert mine[0]["is_example"] is True
    assert mine[0]["status"] == "draft"

    assert client.get("/api/v1/classes/enrolled", headers=_auth(student_token)).json() == []


def test_example_class_cannot_be_published_and_is_not_public(client):
    teacher_token = _register(client, "teacher_ex2@example.com", "teacher")
    example_id = client.get("/api/v1/classes/mine", headers=_auth(teacher_token)).json()[0]["id"]

    resp = client.post(f"/api/v1/classes/{example_id}/publish", headers=_auth(teacher_token))
    assert resp.status_code == 400

    public = client.get("/api/v1/classes", headers=_auth(teacher_token)).json()
    assert example_id not in [c["id"] for c in public]


def test_example_class_is_elementary_with_lessons_boss_and_sources(client):
    token = _register(client, "teacher_ex3@example.com", "teacher")
    mine = client.get("/api/v1/classes/mine", headers=_auth(token)).json()
    assert mine[0]["title"] == "Contoh: IPA Kelas 4 - Siklus Air"
    class_id = mine[0]["id"]

    levels = client.get(f"/api/v1/classes/{class_id}/levels", headers=_auth(token)).json()
    assert [lv["type"] for lv in levels] == ["lesson_quiz"] * 3 + ["boss"]
    assert [lv["status"] for lv in levels] == ["approved", "draft", "draft", "draft"]
    for lv in levels[:3]:
        assert 400 <= len(lv["content"].split()) <= 700
        assert lv["content"].count("### ") >= 2
        assert lv["summary"] and len(lv["key_points"]) == 5
        assert len(lv["sources"]) == 1
        assert lv["sources"][0]["section_title"] == lv["title"]
    assert levels[3]["content"] is None
    assert len(levels[3]["sources"]) == 3


def test_example_class_questions_are_valid(client, db):
    token = _register(client, "teacher_ex4@example.com", "teacher")
    class_id = client.get("/api/v1/classes/mine", headers=_auth(token)).json()[0]["id"]
    levels = db.query(Level).filter(Level.class_id == uuid.UUID(class_id)).all()
    assert len(levels) == 4
    for level in levels:
        questions = db.query(Question).filter(Question.level_id == level.id).all()
        assert len(questions) == 5
        for q in questions:
            assert len(q.options) == 4
            assert q.correct_answer in q.options
            expected = QuestionStatus.approved if level.order_index == 0 else QuestionStatus.draft
            assert q.status == expected
            if level.type == LevelType.lesson_quiz:
                assert q.source_chunk_id is not None


def test_example_class_cannot_be_generated(client, db):
    token = _register(client, "teacher_ex5@example.com", "teacher")
    class_id = client.get("/api/v1/classes/mine", headers=_auth(token)).json()[0]["id"]
    resp = client.post(f"/api/v1/classes/{class_id}/levels/generate", headers=_auth(token))
    assert resp.status_code == 400
