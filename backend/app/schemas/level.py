from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.level import LevelStatus, LevelType

MAX_KEY_POINTS = 8
MAX_CONTENT_CHARS = 20000
MAX_SOURCES = 12


class LevelSourceResponse(BaseModel):
    chunk_id: UUID
    section_title: str | None
    page_start: int
    page_end: int


class ChunkOptionResponse(BaseModel):
    """A section of the class materials that a teacher can pick as a level source."""

    id: UUID
    section_title: str | None
    page_start: int
    page_end: int
    material_name: str


class LevelResponse(BaseModel):
    id: UUID
    class_id: UUID
    prerequisite_id: UUID | None
    title: str
    type: LevelType
    order_index: int
    content: str | None = None
    summary: str | None
    key_points: list[str] = []
    sources: list[LevelSourceResponse] = []
    status: LevelStatus

    model_config = {"from_attributes": True}


class LevelUpdateRequest(BaseModel):
    title: str | None = None
    order_index: int | None = None
    prerequisite_id: UUID | None = None
    clear_prerequisite: bool = False
    status: LevelStatus | None = None
    summary: str | None = None
    content: str | None = None
    key_points: list[str] | None = None
    # Replaces the level's source sections; every id must be a chunk of the same class.
    source_chunk_ids: list[UUID] | None = None

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > MAX_CONTENT_CHARS:
            raise ValueError(f"content maksimal {MAX_CONTENT_CHARS} karakter")
        return value.strip()

    @field_validator("source_chunk_ids")
    @classmethod
    def _validate_sources(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None
        if len(value) > MAX_SOURCES:
            raise ValueError(f"sumber maksimal {MAX_SOURCES} bagian")
        return list(dict.fromkeys(value))

    @field_validator("key_points")
    @classmethod
    def _validate_key_points(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if len(value) > MAX_KEY_POINTS:
            raise ValueError(f"key_points maksimal {MAX_KEY_POINTS} item")
        stripped = [point.strip() for point in value]
        if any(not point for point in stripped):
            raise ValueError("key_points tidak boleh kosong")
        return stripped
