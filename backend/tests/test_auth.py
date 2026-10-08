def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Budi",
            "email": "budi@example.com",
            "password": "secret123",
            "role": "teacher",
        },
    )
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp = client.post(
        "/api/v1/auth/login", json={"email": "budi@example.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "budi@example.com"


def test_register_duplicate_email_rejected(client):
    payload = {
        "name": "Budi",
        "email": "dup@example.com",
        "password": "secret123",
        "role": "student",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Siti",
            "email": "siti@example.com",
            "password": "correct123",
            "role": "student",
        },
    )
    resp = client.post(
        "/api/v1/auth/login", json={"email": "siti@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_me_without_token_rejected(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)
