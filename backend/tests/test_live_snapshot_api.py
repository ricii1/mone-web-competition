from app.core.security import create_access_token
from tests.test_live_session import _setup


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


def test_live_rest_snapshot_requires_host_or_participant(client, db):
    from app.models.live_session import LiveParticipant

    teacher, student, session, _ = _setup(db)
    response = client.get(f"/api/v1/live-sessions/{session.id}", headers=_headers(student))
    assert response.status_code == 200
    assert response.json()["participants"][0]["name"] == student.name
    assert response.json()["question"] is None
    db.query(LiveParticipant).filter_by(live_session_id=session.id).delete()
    db.commit()
    assert (
        client.get(f"/api/v1/live-sessions/{session.id}", headers=_headers(student)).status_code
        == 403
    )
    assert (
        client.get(f"/api/v1/live-sessions/{session.id}", headers=_headers(teacher)).status_code
        == 200
    )


def test_rest_snapshot_rejoins_running_and_finished_question(client, db):
    teacher, student, session, question = _setup(db)
    url = f"/api/v1/live-sessions/{session.id}"
    assert client.post(f"{url}/start", headers=_headers(teacher)).status_code == 204
    snapshot = client.get(url, headers=_headers(student)).json()
    assert snapshot["question"]["question_id"] == str(question.id)
    assert "correct_answer" not in snapshot["question"]
    assert snapshot["closed_question"] is None
    assert (
        client.post(
            f"{url}/answer",
            headers=_headers(student),
            json={
                "question_id": str(question.id),
                "answer": "4",
            },
        ).status_code
        == 204
    )
    assert client.get(url, headers=_headers(student)).json()["my_answer"] == "4"
    assert client.post(f"{url}/end", headers=_headers(teacher)).status_code == 204
    snapshot = client.get(url, headers=_headers(student)).json()
    assert snapshot["closed_question"]["correct_answer"] == "4"
    assert snapshot["my_answer"] == "4"
    assert snapshot["participants"][0]["score"] >= 100
