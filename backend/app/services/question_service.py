from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.level import Level
from app.models.progress import Attempt, ProgressStatus
from app.models.question import Question, QuestionStatus
from app.schemas.question import QuestionCreateRequest, QuestionUpdateRequest, QuizSubmitResponse
from app.services.leaderboard_service import on_best_score_changed
from app.services.progress_service import PASSING_SCORE, get_or_create_progress, record_quiz_result


def list_questions_for_level(db: Session, level_id: UUID, approved_only: bool) -> list[Question]:
    query = db.query(Question).filter(Question.level_id == level_id)
    if approved_only:
        query = query.filter(Question.status == QuestionStatus.approved)
    return query.all()


def get_question_or_404(db: Session, question_id: UUID) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soal tidak ditemukan")
    return question


def create_question(db: Session, level_id: UUID, body: QuestionCreateRequest) -> Question:
    question = Question(
        level_id=level_id,
        question_text=body.question_text,
        options=body.options,
        correct_answer=body.correct_answer,
        explanation=body.explanation,
        status=QuestionStatus.draft,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(db: Session, question: Question, body: QuestionUpdateRequest) -> Question:
    for field in ("question_text", "options", "correct_answer", "explanation", "status"):
        value = getattr(body, field)
        if value is not None:
            setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question: Question) -> None:
    db.delete(question)
    db.commit()


async def submit_quiz(
    db: Session, student_id: UUID, level: Level, answers: dict[UUID, str]
) -> QuizSubmitResponse:
    progress = get_or_create_progress(db, student_id, level.id)
    if progress.status == ProgressStatus.locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Level masih terkunci")

    approved_questions = list_questions_for_level(db, level.id, approved_only=True)
    if not approved_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Level ini belum punya soal approved"
        )

    correct_count = 0
    for question in approved_questions:
        user_answer = answers.get(question.id, "")
        is_correct = user_answer == question.correct_answer
        if is_correct:
            correct_count += 1
        db.add(
            Attempt(
                user_id=student_id,
                question_id=question.id,
                user_answer=user_answer,
                is_correct=is_correct,
            )
        )
    db.commit()

    total_count = len(approved_questions)
    score_percent = round(correct_count / total_count * 100)
    record_quiz_result(db, student_id, level.id, score_percent)
    await on_best_score_changed(db, level.class_id)

    return QuizSubmitResponse(
        score_percent=score_percent,
        passed=score_percent >= PASSING_SCORE,
        correct_count=correct_count,
        total_count=total_count,
    )
