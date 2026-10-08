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
    assert titles == ["Draft Class"]


def test_student_cannot_list_owned_classes(client):
    student_token = _register(client, "student_own@example.com", "student")
    resp = client.get("/api/v1/classes/mine", headers=_auth(student_token))
    assert resp.status_code == 403
