import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.class_ import Class
from app.models.material import Material, VectorStatus


async def save_uploaded_pdf(db: Session, cls: Class, file: UploadFile) -> Material:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File harus berformat PDF"
        )

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ukuran file melebihi batas {settings.max_upload_mb}MB",
        )

    upload_dir = Path(settings.upload_dir) / str(cls.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    file_path = upload_dir / f"{file_id}.pdf"
    file_path.write_bytes(content)

    material = Material(
        class_id=cls.id,
        file_name=file.filename or "materi.pdf",
        file_path=str(file_path),
        vector_status=VectorStatus.pending,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material
