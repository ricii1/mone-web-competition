from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.level import LevelStatus, LevelType

MAX_KEY_POINTS = 8
MAX_CONTENT_CHARS = 20000
MAX_SOURCE_NOTE_CHARS = 1000


class LevelSourceResponse(BaseModel):
    section_title: str | None
    page_start: int
    page_end: int


class LevelResponse(BaseModel):
    id: UUID
    class_id: UUID
    prerequisite_id: UUID | None
    title: str
    type: LevelType
    order_index: int
    content: str | None = None
    source_note: str | None = None
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
    source_note: str | None = None
    key_points: list[str] | None = None

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > MAX_CONTENT_CHARS:
            raise ValueError(f"content maksimal {MAX_CONTENT_CHARS} karakter")
        return value.strip()

    @field_validator("source_note")
    @classmethod
    def _validate_source_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > MAX_SOURCE_NOTE_CHARS:
            raise ValueError(f"sumber maksimal {MAX_SOURCE_NOTE_CHARS} karakter")
        return value.strip()

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
