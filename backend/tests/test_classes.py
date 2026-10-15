def _register(client, email, role):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "secret123", "role": role},
    )
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_teacher_creates_and_publishes_class(client):
    token = _register(client, "teacher1@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes",
        json={"title": "Matematika", "visibility": "public"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    class_id = resp.json()["id"]

    resp = client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


def test_other_teacher_cannot_edit_class(client):
    token1 = _register(client, "owner@example.com", "teacher")
    token2 = _register(client, "other@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes", json={"title": "IPA", "visibility": "public"}, headers=_auth(token1)
    )
    class_id = resp.json()["id"]

    resp = client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token2))
    assert resp.status_code == 403


def test_one_account_can_teach_and_learn(client):
    """Like Kahoot: same account creates a class and joins another as a student."""
    owner = _register(client, "owner_dual@example.com", "teacher")
    dual = _register(client, "dual@example.com", "student")  # default role is only a default

    created = client.post(
        "/api/v1/classes", json={"title": "Bahasa", "visibility": "public"}, headers=_auth(dual)
    )
    assert created.status_code == 201

    other = client.post(
        "/api/v1/classes", json={"title": "IPA", "visibility": "public"}, headers=_auth(owner)
    ).json()["id"]
    client.post(f"/api/v1/classes/{other}/publish", headers=_auth(owner))

    assert (
        client.post(f"/api/v1/classes/{other}/join", json={}, headers=_auth(dual)).status_code
        == 204
    )
    # joining as a student does not grant ownership
    resp = client.post(f"/api/v1/classes/{other}/publish", headers=_auth(dual))
    assert resp.status_code == 403


def test_join_private_class_requires_correct_invite_code(client):
    teacher_token = _register(client, "teacher2@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes",
        json={"title": "Fisika", "visibility": "private"},
        headers=_auth(teacher_token),
    )
    class_id = resp.json()["id"]
    invite_code = resp.json()["invite_code"]
    client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(teacher_token))

    student_token = _register(client, "student2@example.com", "student")

    resp = client.post(
        f"/api/v1/classes/{class_id}/join",
        json={"invite_code": "WRONG"},
        headers=_auth(student_token),
    )
    assert resp.status_code == 403

    resp = client.post(
        f"/api/v1/classes/{class_id}/join",
        json={"invite_code": invite_code},
        headers=_auth(student_token),
    )
    assert resp.status_code == 204


def test_invite_code_hidden_from_non_owner(client):
    teacher_token = _register(client, "teacher3@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes",
        json={"title": "Kimia", "visibility": "private"},
        headers=_auth(teacher_token),
    )
    class_id = resp.json()["id"]
    client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(teacher_token))

    other_token = _register(client, "teacher4@example.com", "teacher")
    resp = client.get(f"/api/v1/classes/{class_id}", headers=_auth(other_token))
    assert resp.json()["invite_code"] is None


def test_publish_requires_both_lesson_and_question_approval(client, db):
    import uuid

    from app.models.class_ import Class
    from app.models.level import Level, LevelStatus, LevelType
    from app.models.question import Question, QuestionStatus

    token = _register(client, "review@example.com", "teacher")
    class_id = client.post(
        "/api/v1/classes", json={"title": "Air", "visibility": "public"}, headers=_auth(token)
    ).json()["id"]
    level = Level(
        class_id=uuid.UUID(class_id), title="Sumber Air", type=LevelType.lesson_quiz, order_index=0
    )
    db.add(level)
    db.commit()
    question = Question(
        level_id=level.id,
        question_text="Apa?",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        status=QuestionStatus.approved,
    )
    db.add(question)
    db.commit()
    response = client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token))
    assert response.status_code == 400
    assert "materi belum disetujui" in response.json()["detail"]
    assert db.get(Class, uuid.UUID(class_id)).status.value == "draft"
    assert (
        client.patch(
            f"/api/v1/levels/{level.id}", json={"status": "approved"}, headers=_auth(token)
        ).status_code
        == 200
    )
    question.status = QuestionStatus.draft
    db.commit()
    response = client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token))
    assert response.status_code == 400
    assert "soal yang disetujui" in response.json()["detail"]
    question.status = QuestionStatus.approved
    db.commit()
    assert level.status == LevelStatus.approved
    assert (
        client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token)).status_code == 200
    )


def test_publish_rejects_running_generation(client, db):
    import uuid

    from app.models.class_ import Class, GenerationStatus

    token = _register(client, "running@example.com", "teacher")
    class_id = client.post(
        "/api/v1/classes", json={"title": "Air", "visibility": "public"}, headers=_auth(token)
    ).json()["id"]
    cls = db.get(Class, uuid.UUID(class_id))
    cls.generation_status = GenerationStatus.generating
    db.commit()
    assert (
        client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(token)).status_code == 400
    )
