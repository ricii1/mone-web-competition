from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_student, require_teacher
from app.db.session import get_db
from app.models.class_ import ClassStatus
from app.models.user import User
from app.schemas.question import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionTeacherResponse,
    QuestionUpdateRequest,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services import class_service, level_service, question_service

router = APIRouter(tags=["questions"])


@router.get("/api/v1/levels/{level_id}/questions")
def list_questions(
    level_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[QuestionTeacherResponse] | list[QuestionResponse]:
    level = level_service.get_level_or_404(db, level_id)
    cls = class_service.get_class_or_404(db, level.class_id)
    is_owner = cls.teacher_id == user.id

    if is_owner:
        questions = question_service.list_questions_for_level(db, level_id, approved_only=False)
        return [QuestionTeacherResponse.model_validate(q) for q in questions]

    if cls.status != ClassStatus.published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Class belum dipublikasikan"
        )
    if not class_service.is_enrolled(db, user.id, cls.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini")

    questions = question_service.list_questions_for_level(db, level_id, approved_only=True)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.post(
    "/api/v1/levels/{level_id}/questions",
    response_model=QuestionTeacherResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    level_id: UUID,
    body: QuestionCreateRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    level = level_service.get_level_or_404(db, level_id)
    cls = class_service.get_class_or_404(db, level.class_id)
    class_service.require_owner(cls, teacher)
    return question_service.create_question(db, level_id, body)


def _require_question_owner(db: Session, question_id: UUID, teacher: User):
    question = question_service.get_question_or_404(db, question_id)
    level = level_service.get_level_or_404(db, question.level_id)
    cls = class_service.get_class_or_404(db, level.class_id)
    class_service.require_owner(cls, teacher)
    return question


@router.patch("/api/v1/questions/{question_id}", response_model=QuestionTeacherResponse)
def update_question(
    question_id: UUID,
    body: QuestionUpdateRequest,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    question = _require_question_owner(db, question_id, teacher)
    return question_service.update_question(db, question, body)


@router.delete("/api/v1/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: UUID, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)
) -> None:
    question = _require_question_owner(db, question_id, teacher)
    question_service.delete_question(db, question)


@router.post("/api/v1/levels/{level_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    level_id: UUID,
    body: QuizSubmitRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    level = level_service.get_level_or_404(db, level_id)
    cls = class_service.get_class_or_404(db, level.class_id)
    if cls.status != ClassStatus.published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Class belum dipublikasikan"
        )
    if not class_service.is_enrolled(db, student.id, cls.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Belum join class ini")
    return await question_service.submit_quiz(db, student.id, level, body.answers)
