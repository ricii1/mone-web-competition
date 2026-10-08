from uuid import UUID

from pydantic import BaseModel

from app.models.live_session import LiveSessionStatus


class LiveSessionCreateRequest(BaseModel):
    level_id: UUID


class LiveSessionResponse(BaseModel):
    id: UUID
    class_id: UUID
    level_id: UUID
    host_id: UUID
    join_code: str
    status: LiveSessionStatus
    current_question_index: int

    model_config = {"from_attributes": True}


class LiveJoinRequest(BaseModel):
    join_code: str


class LiveAnswerRequest(BaseModel):
    question_id: UUID
    answer: str
