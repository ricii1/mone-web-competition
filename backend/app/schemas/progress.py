from uuid import UUID

from pydantic import BaseModel

from app.models.progress import ProgressStatus


class ProgressResponse(BaseModel):
    level_id: UUID
    status: ProgressStatus
    best_score: int

    model_config = {"from_attributes": True}
