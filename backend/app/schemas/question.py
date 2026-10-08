from uuid import UUID

from pydantic import BaseModel

from app.models.question import QuestionStatus, QuestionType


class QuestionResponse(BaseModel):
    id: UUID
    level_id: UUID
    question_text: str
    question_type: QuestionType
    options: list[str]
    explanation: str | None
    status: QuestionStatus

    model_config = {"from_attributes": True}


class QuestionTeacherResponse(QuestionResponse):
    correct_answer: str


class QuestionCreateRequest(BaseModel):
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: str | None = None


class QuestionUpdateRequest(BaseModel):
    question_text: str | None = None
    options: list[str] | None = None
    correct_answer: str | None = None
    explanation: str | None = None
    status: QuestionStatus | None = None


class QuizSubmitRequest(BaseModel):
    answers: dict[UUID, str]


class QuestionResult(BaseModel):
    question_id: UUID
    your_answer: str | None
    is_correct: bool
    correct_answer: str
    explanation: str | None


class QuizSubmitResponse(BaseModel):
    score_percent: int
    passed: bool
    correct_count: int
    total_count: int
    results: list[QuestionResult] = []
