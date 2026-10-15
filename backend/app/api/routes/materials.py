from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_teacher
from app.db.session import get_db
from app.models.class_ import Class, ClassStatus
from app.models.material import Material, MaterialChunk
from app.models.user import User
from app.schemas.material import (
    MaterialResponse,
    MaterialSectionContent,
    MaterialSectionsResponse,
)
from app.services import class_service, material_service
from app.services.resource_deletion import delete_failed_material

router = APIRouter(prefix="/api/v1/classes/{class_id}/materials", tags=["materials"])


def _require_access(db: Session, class_id: UUID, user: User) -> Class:
    cls = class_service.get_class_or_404(db, class_id)
    is_owner = cls.teacher_id == user.id
    is_enrolled = class_service.is_enrolled(db, user.id, class_id)
    if not is_owner and (not is_enrolled or cls.status != ClassStatus.published):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tidak punya akses ke class ini"
        )
    return cls


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    class_id: UUID,
    file: UploadFile,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> Material:
    cls = class_service.get_class_or_404(db, class_id)
    class_service.require_owner(cls, teacher)

    material = await material_service.save_uploaded_pdf(db, cls, file)

    await material_service.enqueue_material(db, material)

    return material


@router.get("", response_model=list[MaterialResponse])
def list_materials(
    class_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Material]:
    cls = _require_access(db, class_id, user)
    return db.query(Material).filter(Material.class_id == cls.id).all()


@router.get("/{material_id}/file")
def view_material_pdf(
    class_id: UUID,
    material_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    _require_access(db, class_id, user)
    path, filename = material_service.get_material_pdf_path(db, class_id, material_id)
    db.close()
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/{material_id}/retry", response_model=MaterialResponse)
async def retry_material(
    class_id: UUID,
    material_id: UUID,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> Material:
    material = material_service.prepare_material_retry(db, class_id, material_id, teacher)
    await material_service.enqueue_material(db, material)
    db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=204)
async def remove_material(
    class_id: UUID,
    material_id: UUID,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> None:
    await delete_failed_material(db, class_id, material_id, teacher)


@router.get("/{material_id}/sections", response_model=MaterialSectionsResponse)
def preview_sections(
    class_id: UUID,
    material_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> MaterialSectionsResponse:
    return material_service.list_material_sections(
        db, class_id, material_id, teacher, offset, limit
    )


@router.get("/{material_id}/sections/{chunk_id}", response_model=MaterialSectionContent)
def preview_section_content(
    class_id: UUID,
    material_id: UUID,
    chunk_id: UUID,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> MaterialChunk:
    return material_service.get_material_section(db, class_id, material_id, chunk_id, teacher)
