from uuid import UUID

from pydantic import BaseModel

from app.models.level import LevelStatus, LevelType


class LevelResponse(BaseModel):
    id: UUID
    class_id: UUID
    prerequisite_id: UUID | None
    title: str
    type: LevelType
    order_index: int
    summary: str | None
    status: LevelStatus

    model_config = {"from_attributes": True}


class LevelUpdateRequest(BaseModel):
    title: str | None = None
    order_index: int | None = None
    prerequisite_id: UUID | None = None
    clear_prerequisite: bool = False
    status: LevelStatus | None = None
