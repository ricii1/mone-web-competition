def _register(client, email, role):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "secret123", "role": role},
    )
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_enrolled_classes_only_shows_joined(client):
    teacher_token = _register(client, "teacher_enr@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes", json={"title": "A", "visibility": "public"}, headers=_auth(teacher_token)
    )
    class_a = resp.json()["id"]
    resp = client.post(
        "/api/v1/classes", json={"title": "B", "visibility": "public"}, headers=_auth(teacher_token)
    )
    class_b = resp.json()["id"]
    client.post(f"/api/v1/classes/{class_a}/publish", headers=_auth(teacher_token))
    client.post(f"/api/v1/classes/{class_b}/publish", headers=_auth(teacher_token))

    student_token = _register(client, "student_enr@example.com", "student")
    client.post(f"/api/v1/classes/{class_a}/join", json={}, headers=_auth(student_token))

    resp = client.get("/api/v1/classes/enrolled", headers=_auth(student_token))
    assert resp.status_code == 200
    titles = [c["title"] for c in resp.json()]
    assert titles == ["A"]
