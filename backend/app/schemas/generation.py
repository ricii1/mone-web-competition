from pydantic import BaseModel, Field


class GeneratedLevelSummary(BaseModel):
    summary: str


class GeneratedQuestion(BaseModel):
    question_text: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str


class GeneratedQuestionsOutput(BaseModel):
    questions: list[GeneratedQuestion]
