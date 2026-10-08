from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_teacher
from app.db.session import get_db
from app.models.material import Material
from app.models.user import User, UserRole
from app.schemas.material import MaterialResponse
from app.services import class_service, material_service
from app.worker.queue import get_arq_pool

router = APIRouter(prefix="/api/v1/classes/{class_id}/materials", tags=["materials"])


def _require_access(db: Session, class_id: UUID, user: User):
    cls = class_service.get_class_or_404(db, class_id)
    is_owner = cls.teacher_id == user.id
    is_enrolled = user.role == UserRole.student and class_service.is_enrolled(db, user.id, class_id)
    if not (is_owner or is_enrolled):
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

    pool = await get_arq_pool()
    await pool.enqueue_job("process_material", str(material.id))

    return material


@router.get("", response_model=list[MaterialResponse])
def list_materials(
    class_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Material]:
    cls = _require_access(db, class_id, user)
    return db.query(Material).filter(Material.class_id == cls.id).all()
