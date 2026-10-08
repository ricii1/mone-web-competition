from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MaterialStage = Literal[
    "reading",
    "chunking",
    "embedding",
    "generating_levels",
    "generating_questions",
    "done",
    "failed",
]

GenerationStage = Literal["generating_levels", "generating_questions", "done", "failed"]

EventType = Literal[
    "material_progress",
    "generation_progress",
    "level_created",
    "leaderboard_updated",
    "live_session_update",
]


class RealtimeEvent(BaseModel):
    type: EventType
    payload: dict[str, Any]
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MaterialProgressPayload(BaseModel):
    material_id: str
    stage: MaterialStage
    current: int = 0
    total: int = 0
    error_message: str | None = None


class GenerationProgressPayload(BaseModel):
    class_id: str
    stage: GenerationStage
    current: int = 0
    total: int = 0
    error_message: str | None = None


class LevelCreatedPayload(BaseModel):
    level_id: str
    class_id: str
    title: str
    order_index: int


class LeaderboardUpdatedPayload(BaseModel):
    class_id: str


class LiveSessionUpdatePayload(BaseModel):
    session_id: str
    status: str
    current_question_index: int
