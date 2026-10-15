import uuid

import pytest

from app.core.config import settings
from app.core.security import create_access_token
from app.models.class_ import ClassStatus, Enrollment
from app.models.material import Material
from app.models.user import UserRole
from tests.test_live_session import _setup, _user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


@pytest.fixture
def pdf(db, tmp_path, monkeypatch):
    from app.models.class_ import Class

    teacher, student, session, _ = _setup(db)
    cls = db.get(Class, session.class_id)
    cls.status = ClassStatus.published
    db.add(Enrollment(class_id=cls.id, user_id=student.id))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    directory = tmp_path / str(cls.id)
    directory.mkdir()
    path = directory / "source.pdf"
    path.write_bytes(b"%PDF-1.4\noriginal teacher material")
    material = Material(class_id=cls.id, file_name="Materi asli.pdf", file_path=str(path))
    db.add(material)
    db.commit()
    return cls, teacher, student, material, path


@pytest.mark.parametrize("role", ["teacher", "student"])
def test_owner_and_enrolled_student_can_view_original_pdf(client, pdf, role):
    cls, teacher, student, material, path = pdf
    user = teacher if role == "teacher" else student
    response = client.get(
        f"/api/v1/classes/{cls.id}/materials/{material.id}/file", headers=_headers(user)
    )
    assert response.status_code == 200
    assert response.content == path.read_bytes()
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.headers["cache-control"] == "private, no-store"


def test_pdf_requires_auth_and_class_access(client, db, pdf):
    cls, _, _, material, _ = pdf
    url = f"/api/v1/classes/{cls.id}/materials/{material.id}/file"
    assert client.get(url).status_code == 401
    outsider = _user(db, UserRole.teacher)
    assert client.get(url, headers=_headers(outsider)).status_code == 403


def test_student_cannot_view_pdf_when_class_unpublished(client, db, pdf):
    cls, teacher, student, material, _ = pdf
    cls.status = ClassStatus.draft
    db.commit()
    url = f"/api/v1/classes/{cls.id}/materials/{material.id}/file"
    assert client.get(url, headers=_headers(student)).status_code == 403
    assert client.get(url, headers=_headers(teacher)).status_code == 200
    assert (
        client.get(f"/api/v1/classes/{cls.id}/materials", headers=_headers(student)).status_code
        == 403
    )


def test_cross_class_material_and_missing_file_are_rejected(client, db, pdf):
    from app.models.class_ import Class, ClassVisibility

    cls, teacher, _, material, path = pdf
    other = Class(teacher_id=teacher.id, title="Other", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    assert (
        client.get(
            f"/api/v1/classes/{other.id}/materials/{material.id}/file", headers=_headers(teacher)
        ).status_code
        == 404
    )
    path.unlink()
    assert (
        client.get(
            f"/api/v1/classes/{cls.id}/materials/{material.id}/file", headers=_headers(teacher)
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/classes/{cls.id}/materials/{uuid.uuid4()}/file", headers=_headers(teacher)
        ).status_code
        == 404
    )


def test_pdf_cannot_escape_class_upload_directory(client, db, pdf, tmp_path):
    cls, teacher, _, material, path = pdf
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-secret")
    path.unlink()
    path.symlink_to(outside)
    assert (
        client.get(
            f"/api/v1/classes/{cls.id}/materials/{material.id}/file", headers=_headers(teacher)
        ).status_code
        == 404
    )
