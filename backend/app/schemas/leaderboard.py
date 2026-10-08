from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: UUID
    name: str
    score: int
