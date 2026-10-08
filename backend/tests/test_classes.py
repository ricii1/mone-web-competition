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


def test_student_cannot_create_class(client):
    token = _register(client, "student1@example.com", "student")
    resp = client.post(
        "/api/v1/classes", json={"title": "Bahasa", "visibility": "public"}, headers=_auth(token)
    )
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
