from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_student, require_teacher
from app.db.session import get_db
from app.models.class_ import ClassStatus
from app.models.user import User
from app.schemas.class_ import ClassCreateRequest, ClassJoinRequest, ClassResponse
from app.services import class_service, level_service

router = APIRouter(prefix="/api/v1/classes", tags=["classes"])


def _to_response(cls, viewer: User) -> ClassResponse:
    data = ClassResponse.model_validate(cls)
    if cls.teacher_id != viewer.id:
        data.invite_code = None
    return data


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    body: ClassCreateRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> ClassResponse:
    cls = class_service.create_class(db, teacher, body)
    return _to_response(cls, teacher)


@router.get("", response_model=list[ClassResponse])
def list_classes(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ClassResponse]:
    classes = class_service.list_public_classes(db)
    return [_to_response(c, user) for c in classes]


@router.get("/enrolled", response_model=list[ClassResponse])
def list_enrolled_classes(
    student: User = Depends(require_student), db: Session = Depends(get_db)
) -> list[ClassResponse]:
    classes = class_service.list_enrolled_classes(db, student.id)
    return [_to_response(c, student) for c in classes]


@router.get("/mine", response_model=list[ClassResponse])
def list_owned_classes(
    teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> list[ClassResponse]:
    classes = class_service.list_owned_classes(db, teacher.id)
    return [_to_response(c, teacher) for c in classes]


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ClassResponse:
    cls = class_service.get_class_or_404(db, class_id)
    return _to_response(cls, user)


@router.post("/{class_id}/publish", response_model=ClassResponse)
def publish_class(
    class_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> ClassResponse:
    cls = class_service.get_class_or_404(db, class_id)
    class_service.require_owner(cls, teacher)
    if cls.is_example:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class contoh tidak bisa dipublish. Buat class baru untuk materimu sendiri.",
        )
    blockers = level_service.class_publish_blockers(db, class_id)
    if blockers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Level berikut belum punya soal approved: {', '.join(blockers)}",
        )
    cls.status = ClassStatus.published
    db.commit()
    db.refresh(cls)
    return _to_response(cls, teacher)


@router.post("/{class_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def join_class(
    class_id: UUID,
    body: ClassJoinRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> None:
    class_service.join_class(db, student, class_id, body.invite_code)
