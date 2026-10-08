from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_teacher
from app.db.session import get_db
from app.models.class_ import ClassStatus
from app.models.level import Level
from app.models.user import User, UserRole
from app.schemas.level import LevelResponse, LevelUpdateRequest
from app.services import class_service, level_service
from app.worker.queue import get_arq_pool

router = APIRouter(tags=["levels"])


@router.post("/api/v1/classes/{class_id}/levels/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_levels(
    class_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> dict[str, str]:
    cls = class_service.get_class_or_404(db, class_id)
    class_service.require_owner(cls, teacher)

    level_service.request_generation(db, cls)

    pool = await get_arq_pool()
    await pool.enqueue_job("generate_levels_and_questions", str(class_id))
    return {"status": "queued"}


@router.get("/api/v1/classes/{class_id}/levels", response_model=list[LevelResponse])
def list_levels(
    class_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Level]:
    cls = class_service.get_class_or_404(db, class_id)
    is_owner = cls.teacher_id == user.id
    if not is_owner:
        if cls.status != ClassStatus.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Class belum dipublikasikan"
            )
        if user.role == UserRole.student and not class_service.is_enrolled(db, user.id, class_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini"
            )
    return level_service.list_levels_for_class(db, class_id)


def _require_level_owner(db: Session, level_id: UUID, teacher: User) -> Level:
    level = level_service.get_level_or_404(db, level_id)
    cls = class_service.get_class_or_404(db, level.class_id)
    class_service.require_owner(cls, teacher)
    return level


@router.patch("/api/v1/levels/{level_id}", response_model=LevelResponse)
def update_level(
    level_id: UUID,
    body: LevelUpdateRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> Level:
    level = _require_level_owner(db, level_id, teacher)
    return level_service.update_level(db, level, body)


@router.delete("/api/v1/levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_level(
    level_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> None:
    level = _require_level_owner(db, level_id, teacher)
    level_service.delete_level(db, level)
