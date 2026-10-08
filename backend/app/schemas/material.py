from uuid import UUID

from pydantic import BaseModel

from app.models.material import VectorStatus


class MaterialResponse(BaseModel):
    id: UUID
    class_id: UUID
    file_name: str
    vector_status: VectorStatus
    error_message: str | None

    model_config = {"from_attributes": True}
