import uuid

from starlette.websockets import WebSocketDisconnect


def _register(client, email, role):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "secret123", "role": role},
    )
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_websocket_without_token_is_rejected(client):
    fake_class_id = uuid.uuid4()
    try:
        with client.websocket_connect(f"/ws/classes/{fake_class_id}"):
            raise AssertionError("koneksi seharusnya ditolak tanpa token")
    except WebSocketDisconnect as exc:
        assert exc.code in (4401, 4403)


def test_student_cannot_access_material_of_class_not_joined(client):
    teacher_token = _register(client, "teacher_mat@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes",
        json={"title": "Sejarah", "visibility": "public"},
        headers=_auth(teacher_token),
    )
    class_id = resp.json()["id"]
    client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(teacher_token))

    student_token = _register(client, "student_mat@example.com", "student")
    resp = client.get(f"/api/v1/classes/{class_id}/materials", headers=_auth(student_token))
    assert resp.status_code == 403


def test_student_join_class_grants_material_list_access(client):
    teacher_token = _register(client, "teacher_mat2@example.com", "teacher")
    resp = client.post(
        "/api/v1/classes",
        json={"title": "Geografi", "visibility": "public"},
        headers=_auth(teacher_token),
    )
    class_id = resp.json()["id"]
    client.post(f"/api/v1/classes/{class_id}/publish", headers=_auth(teacher_token))

    student_token = _register(client, "student_mat2@example.com", "student")
    client.post(f"/api/v1/classes/{class_id}/join", json={}, headers=_auth(student_token))

    resp = client.get(f"/api/v1/classes/{class_id}/materials", headers=_auth(student_token))
    assert resp.status_code == 200
