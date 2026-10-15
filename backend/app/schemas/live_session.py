from uuid import UUID

from pydantic import BaseModel

from app.models.live_session import LiveSessionStatus


class LiveSessionCreateRequest(BaseModel):
    level_id: UUID


class LiveQuestionResponse(BaseModel):
    question_id: UUID
    question_text: str
    options: list[str]
    index: int
    total: int
    deadline: float
    time_limit_seconds: int


class LiveClosedQuestionResponse(BaseModel):
    question_id: UUID
    correct_answer: str
    distribution: dict[str, int]
    finished: bool


class LiveParticipantResponse(BaseModel):
    user_id: UUID
    name: str
    score: int


class LiveSessionResponse(BaseModel):
    id: UUID
    class_id: UUID
    level_id: UUID
    host_id: UUID
    join_code: str
    status: LiveSessionStatus
    current_question_index: int

    question: LiveQuestionResponse | None = None
    closed_question: LiveClosedQuestionResponse | None = None
    my_answer: str | None = None
    participants: list[LiveParticipantResponse] = []

    model_config = {"from_attributes": True}


class LiveJoinRequest(BaseModel):
    join_code: str


class LiveAnswerRequest(BaseModel):
    question_id: UUID
    answer: str


class LiveNextRequest(BaseModel):
    question_id: UUID | None = None
