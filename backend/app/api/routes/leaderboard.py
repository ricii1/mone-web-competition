from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.class_ import ClassStatus
from app.models.user import User
from app.schemas.leaderboard import LeaderboardEntryResponse
from app.services import class_service, leaderboard_service

router = APIRouter(prefix="/api/v1/classes/{class_id}/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntryResponse])
async def get_leaderboard(
    class_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[LeaderboardEntryResponse]:
    cls = class_service.get_class_or_404(db, class_id)
    is_owner = cls.teacher_id == user.id
    if not is_owner:
        if cls.status != ClassStatus.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Class belum dipublikasikan"
            )
        if not class_service.is_enrolled(db, user.id, class_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini"
            )

    entries = await leaderboard_service.get_leaderboard(db, class_id)
    return [
        LeaderboardEntryResponse(rank=e.rank, user_id=e.user_id, name=e.name, score=e.score)
        for e in entries
    ]
