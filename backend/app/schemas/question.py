from uuid import UUID

from pydantic import BaseModel, model_validator

from app.models.question import QuestionStatus, QuestionType


class QuestionResponse(BaseModel):
    id: UUID
    level_id: UUID
    question_text: str
    question_type: QuestionType
    options: list[str]
    status: QuestionStatus

    model_config = {"from_attributes": True}


class QuestionTeacherResponse(QuestionResponse):
    correct_answer: str
    explanation: str | None


def validate_question_options(options: list[str], correct_answer: str) -> None:
    normalized = ["".join(option.split()).casefold() for option in options]
    if len(options) != 4 or any(not option for option in normalized):
        raise ValueError("Soal harus memiliki empat pilihan jawaban yang tidak kosong")
    if len(set(normalized)) != 4:
        raise ValueError("Pilihan jawaban tidak boleh sama")
    if correct_answer not in options:
        raise ValueError("Jawaban benar harus ada dalam pilihan jawaban")


class QuestionCreateRequest(BaseModel):
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: str | None = None

    @model_validator(mode="after")
    def validate_options(self) -> "QuestionCreateRequest":
        validate_question_options(self.options, self.correct_answer)
        return self


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
