from uuid import UUID

from pydantic import BaseModel

from app.models.class_ import ClassStatus, ClassVisibility, GenerationStatus


class ClassCreateRequest(BaseModel):
    title: str
    description: str | None = None
    visibility: ClassVisibility


class ClassResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    title: str
    description: str | None
    visibility: ClassVisibility
    status: ClassStatus
    invite_code: str | None = None
    is_example: bool = False
    generation_status: GenerationStatus = GenerationStatus.idle
    generation_error: str | None = None

    model_config = {"from_attributes": True}


class ClassJoinRequest(BaseModel):
    invite_code: str | None = None


class ClassDeleteRequest(BaseModel):
    confirm_title: str
