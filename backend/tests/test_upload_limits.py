from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.core.config import settings
from app.models.class_ import Class
from app.models.material import Material
from app.services.material_service import save_uploaded_pdf
from tests.test_worker_material import _setup


def _file(content: bytes) -> UploadFile:
    return UploadFile(
        BytesIO(content), filename="test.pdf", headers=Headers({"content-type": "application/pdf"})
    )


async def test_upload_streams_and_removes_oversized_file(db, tmp_path, monkeypatch):
    mat = _setup(db)
    cls = db.get(Class, mat.class_id)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    file = _file(b"%PDF-" + b"x" * (2 * 1024 * 1024))
    original_read = file.read
    file.read = AsyncMock(side_effect=original_read)
    with pytest.raises(HTTPException):
        await save_uploaded_pdf(db, cls, file)
    assert file.file.tell() == 1024 * 1024 + 1
    assert all(call.args[0] <= 64 * 1024 for call in file.read.call_args_list)
    assert list(tmp_path.rglob("*.pdf")) == []
    assert db.query(Material).count() == 1


@pytest.mark.parametrize("content", [b"", b"not a PDF"])
async def test_upload_rejects_empty_or_forged_pdf(db, tmp_path, monkeypatch, content):
    mat = _setup(db)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    with pytest.raises(HTTPException):
        await save_uploaded_pdf(db, db.get(Class, mat.class_id), _file(content))
    assert list(tmp_path.rglob("*.pdf")) == []


def test_upload_body_limit_rejects_before_auth_and_read(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    response = client.post(
        "/api/v1/classes/00000000-0000-0000-0000-000000000000/materials",
        content=b"small",
        headers={"Content-Length": str(2 * 1024 * 1024)},
    )
    assert response.status_code == 413


def test_auth_body_limit_without_content_length(client):
    def chunks():
        yield b'{"email":"'
        yield b"a" * (17 * 1024)
        yield b'"}'

    response = client.post(
        "/api/v1/auth/login", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
