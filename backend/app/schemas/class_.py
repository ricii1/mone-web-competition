from uuid import UUID

from pydantic import BaseModel

from app.models.class_ import ClassStatus, ClassVisibility


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

    model_config = {"from_attributes": True}


class ClassJoinRequest(BaseModel):
    invite_code: str | None = None
