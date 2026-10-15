from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_student, require_teacher
from app.db.session import get_db
from app.models.live_session import LiveParticipant, LiveSession
from app.models.user import User
from app.schemas.live_session import (
    LiveAnswerRequest,
    LiveJoinRequest,
    LiveNextRequest,
    LiveSessionCreateRequest,
    LiveSessionResponse,
)
from app.services import class_service, live_session_service
from app.services.level_service import get_level_or_404

router = APIRouter(tags=["live-sessions"])


@router.post(
    "/api/v1/classes/{class_id}/live-sessions",
    response_model=LiveSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_live_session(
    class_id: UUID,
    body: LiveSessionCreateRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> LiveSession:
    cls = class_service.get_class_or_404(db, class_id)
    class_service.require_owner(cls, teacher)
    level = get_level_or_404(db, body.level_id)
    return live_session_service.create_session(db, cls, level, teacher.id)


@router.post("/api/v1/live-sessions/lookup", response_model=LiveSessionResponse)
def lookup_live_session(
    body: LiveJoinRequest, student: User = Depends(require_student), db: Session = Depends(get_db)
) -> LiveSession:
    session = live_session_service.get_session_by_join_code(db, body.join_code)
    if not class_service.is_enrolled(db, student.id, session.class_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini")
    return session


def _require_host(db: Session, session_id: UUID, teacher: User) -> LiveSession:
    session = live_session_service.get_session_or_404(db, session_id)
    if session.host_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bukan host sesi ini")
    return session


@router.get("/api/v1/live-sessions/{session_id}", response_model=LiveSessionResponse)
async def get_live_session(
    session_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> LiveSessionResponse:
    session = live_session_service.get_session_or_404(db, session_id)
    is_host = session.host_id == user.id
    is_participant = (
        db.query(LiveParticipant)
        .filter(LiveParticipant.live_session_id == session_id, LiveParticipant.user_id == user.id)
        .first()
        is not None
    )
    if not (is_host or is_participant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tidak punya akses ke sesi ini"
        )
    snapshot = await live_session_service.session_snapshot(db, session, user.id)
    return LiveSessionResponse.model_validate(
        LiveSessionResponse.model_validate(session).model_dump() | snapshot
    )


@router.post("/api/v1/live-sessions/{session_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_live_session(
    session_id: UUID,
    body: LiveJoinRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> None:
    session = live_session_service.get_session_or_404(db, session_id)
    if not class_service.is_enrolled(db, student.id, session.class_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini")
    live_session_service.join_session(db, session, student.id, body.join_code)
    await live_session_service._publish(session.id, "participant_joined", {})


@router.post("/api/v1/live-sessions/{session_id}/start", status_code=status.HTTP_204_NO_CONTENT)
async def start_live_session(
    session_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> None:
    session = _require_host(db, session_id, teacher)
    await live_session_service.start_session(db, session)


@router.post("/api/v1/live-sessions/{session_id}/next", status_code=status.HTTP_204_NO_CONTENT)
async def next_question(
    session_id: UUID,
    body: LiveNextRequest | None = None,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> None:
    session = _require_host(db, session_id, teacher)
    await live_session_service.close_current_question(
        db, session, question_id=body.question_id if body else None
    )


@router.post("/api/v1/live-sessions/{session_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_live_session(
    session_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> None:
    session = _require_host(db, session_id, teacher)
    await live_session_service.end_session(db, session)


@router.post("/api/v1/live-sessions/{session_id}/answer", status_code=status.HTTP_204_NO_CONTENT)
async def answer_live_question(
    session_id: UUID,
    body: LiveAnswerRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> None:
    session = live_session_service.get_session_or_404(db, session_id)
    is_participant = (
        db.query(LiveParticipant)
        .filter(
            LiveParticipant.live_session_id == session_id, LiveParticipant.user_id == student.id
        )
        .first()
        is not None
    )
    if not is_participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join sesi ini")
    await live_session_service.submit_answer(db, session, student.id, body.question_id, body.answer)
