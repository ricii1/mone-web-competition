from pydantic import BaseModel, Field, field_validator, model_validator

MIN_CONTENT_CHARS = 200


class GeneratedLevelSummary(BaseModel):
    """Summary + key points only (boss levels)."""

    summary: str = Field(min_length=1)
    key_points: list[str] = Field(min_length=3, max_length=6)

    @field_validator("summary")
    @classmethod
    def _summary_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary must not be blank")
        return value

    @field_validator("key_points")
    @classmethod
    def _points_not_blank(cls, value: list[str]) -> list[str]:
        if any(not point.strip() for point in value):
            raise ValueError("key_points items must not be blank")
        return value


class GeneratedLevelLesson(GeneratedLevelSummary):
    """Lesson level: the article plus the recap and key points."""

    content: str = Field(min_length=MIN_CONTENT_CHARS)

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, value: str) -> str:
        if len(value.strip()) < MIN_CONTENT_CHARS:
            raise ValueError("content is too short")
        return value.strip()


class GeneratedQuestion(BaseModel):
    question_text: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str

    @model_validator(mode="after")
    def _answer_must_be_an_option(self) -> "GeneratedQuestion":
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer must be exactly one of options")
        return self


class GeneratedQuestionsOutput(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1)
