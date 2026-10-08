from pydantic import BaseModel, Field, model_validator


class GeneratedLevelSummary(BaseModel):
    summary: str


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
