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


class MaterialSection(BaseModel):
    id: UUID
    section_title: str | None
    order_index: int
    page_start: int
    page_end: int
    excerpt: str
    character_count: int


class MaterialSectionsResponse(BaseModel):
    sections: list[MaterialSection]
    total: int
    offset: int
    limit: int


class MaterialSectionContent(BaseModel):
    id: UUID
    content: str

    model_config = {"from_attributes": True}
