from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_student
from app.db.session import get_db
from app.models.level import Level
from app.models.progress import Progress
from app.models.user import User
from app.schemas.progress import ProgressResponse
from app.services import class_service

router = APIRouter(prefix="/api/v1/classes/{class_id}/progress", tags=["progress"])


@router.get("", response_model=list[ProgressResponse])
def get_my_progress(
    class_id: UUID, student: User = Depends(require_student), db: Session = Depends(get_db)
) -> list[Progress]:
    if not class_service.is_enrolled(db, student.id, class_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini")
    return (
        db.query(Progress)
        .join(Level, Level.id == Progress.level_id)
        .filter(Progress.user_id == student.id, Level.class_id == class_id)
        .all()
    )
