from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.level import Level
from app.models.progress import Progress
from app.models.user import User
from app.realtime.channels import class_channel
from app.realtime.events import LeaderboardUpdatedPayload, RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event

LEADERBOARD_KEY_PREFIX = "leaderboard"
EPOCH_DIVISOR = 1_000_000_000_000.0
FAR_FUTURE_EPOCH = 9_999_999_999.0


@dataclass
class LeaderboardEntry:
    user_id: UUID
    name: str
    score: int
    rank: int


def _redis_key(class_id: UUID) -> str:
    return f"{LEADERBOARD_KEY_PREFIX}:{class_id}"


def compute_leaderboard_from_postgres(
    db: Session, class_id: UUID
) -> list[tuple[UUID, str, int, float]]:
    rows = (
        db.query(
            User.id,
            User.name,
            func.coalesce(func.sum(Progress.best_score), 0).label("total_score"),
            func.max(Progress.completed_at).label("last_completed_at"),
        )
        .join(Progress, Progress.user_id == User.id)
        .join(Level, Level.id == Progress.level_id)
        .filter(Level.class_id == class_id)
        .group_by(User.id, User.name)
        .all()
    )
    results = []
    for user_id, name, total_score, last_completed_at in rows:
        epoch = last_completed_at.timestamp() if last_completed_at else FAR_FUTURE_EPOCH
        results.append((user_id, name, int(total_score), epoch))
    results.sort(key=lambda r: (-r[2], r[3]))
    return results


async def rebuild_leaderboard_cache(db: Session, class_id: UUID) -> None:
    redis = get_redis()
    key = _redis_key(class_id)
    entries = compute_leaderboard_from_postgres(db, class_id)
    await redis.delete(key)
    if entries:
        mapping = {
            f"{user_id}:{name}": total_score - (epoch / EPOCH_DIVISOR)
            for user_id, name, total_score, epoch in entries
        }
        await redis.zadd(key, mapping)


async def get_leaderboard(db: Session, class_id: UUID, limit: int = 50) -> list[LeaderboardEntry]:
    redis = get_redis()
    key = _redis_key(class_id)
    if not await redis.exists(key):
        await rebuild_leaderboard_cache(db, class_id)

    raw = await redis.zrevrange(key, 0, limit - 1, withscores=True)
    entries = []
    for rank, (member, score) in enumerate(raw, start=1):
        user_id_str, _, name = member.partition(":")
        entries.append(
            LeaderboardEntry(user_id=UUID(user_id_str), name=name, score=round(score), rank=rank)
        )
    return entries


async def on_best_score_changed(db: Session, class_id: UUID) -> None:
    await rebuild_leaderboard_cache(db, class_id)
    await publish_event(
        class_channel(class_id),
        RealtimeEvent(
            type="leaderboard_updated",
            payload=LeaderboardUpdatedPayload(class_id=str(class_id)).model_dump(),
        ),
    )
