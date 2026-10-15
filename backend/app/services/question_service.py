from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.level import Level
from app.models.live_session import LiveSession, LiveSessionStatus
from app.models.progress import Attempt, ProgressStatus
from app.models.question import Question, QuestionStatus
from app.schemas.question import (
    QuestionCreateRequest,
    QuestionResult,
    QuestionUpdateRequest,
    QuizSubmitResponse,
    validate_question_options,
)
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


def _require_unique_question(
    db: Session, level_id: UUID, text: str, exclude_id: UUID | None = None
) -> None:
    normalized = " ".join(text.split()).casefold()
    if not normalized:
        raise HTTPException(status_code=422, detail="Pertanyaan tidak boleh kosong")
    db.query(Level).filter(Level.id == level_id).with_for_update().one()
    existing = (
        db.query(Question.id, Question.question_text).filter(Question.level_id == level_id).all()
    )
    if any(
        q.id != exclude_id and " ".join(q.question_text.split()).casefold() == normalized
        for q in existing
    ):
        raise HTTPException(status_code=409, detail="Pertanyaan yang sama sudah ada di level ini")


def create_question(db: Session, level_id: UUID, body: QuestionCreateRequest) -> Question:
    _require_unique_question(db, level_id, body.question_text)
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
    # Refresh after the lock: a concurrent edit may have changed the omitted fields.
    db.query(Level).filter(Level.id == question.level_id).with_for_update().one()
    db.refresh(question, with_for_update=True)
    try:
        validate_question_options(
            body.options if body.options is not None else question.options,
            body.correct_answer if body.correct_answer is not None else question.correct_answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if body.question_text is not None:
        _require_unique_question(db, question.level_id, body.question_text, question.id)
    for field in ("question_text", "options", "correct_answer", "explanation", "status"):
        value = getattr(body, field)
        if value is not None:
            setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question: Question) -> None:
    db.refresh(question, with_for_update=True)
    if (
        db.query(LiveSession.id)
        .filter(
            LiveSession.level_id == question.level_id,
            LiveSession.status.in_([LiveSessionStatus.waiting, LiveSessionStatus.running]),
        )
        .first()
    ):
        raise HTTPException(status_code=409, detail="Akhiri kuis bersama sebelum menghapus soal")
    if db.query(Attempt.id).filter(Attempt.question_id == question.id).first():
        raise HTTPException(status_code=409, detail="Soal sudah dikerjakan dan tidak bisa dihapus")
    try:
        db.delete(question)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Soal sedang digunakan dan tidak bisa dihapus"
        ) from exc


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
    results: list[QuestionResult] = []
    for question in approved_questions:
        submitted = answers.get(question.id)
        user_answer = submitted or ""
        is_correct = user_answer == question.correct_answer
        if is_correct:
            correct_count += 1
        results.append(
            QuestionResult(
                question_id=question.id,
                your_answer=submitted,
                is_correct=is_correct,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
            )
        )
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
        results=results,
    )
