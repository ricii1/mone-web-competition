from dataclasses import dataclass
from uuid import UUID

from redis.exceptions import WatchError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.level import Level
from app.models.progress import Progress
from app.models.user import User
from app.realtime.channels import class_channel
from app.realtime.events import LeaderboardUpdatedPayload, RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event

LEADERBOARD_KEY_PREFIX = "leaderboard"
MAX_EPOCH_MICROSECONDS = 9_999_999_999_999_999
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
    version_key = f"{key}:version"
    while True:
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(version_key)
                entries = compute_leaderboard_from_postgres(db, class_id)
                # Integer scores stay exact; reverse lexicographic order breaks ties by time.
                mapping = {
                    (
                        f"{MAX_EPOCH_MICROSECONDS - round(epoch * 1_000_000):016d}:{user_id}:{name}"
                    ): score
                    for user_id, name, score, epoch in entries
                }
                pipe.multi()
                pipe.delete(key)
                if mapping:
                    pipe.zadd(key, mapping)
                pipe.set(f"{key}:format", "2")
                await pipe.execute()
                return
            except WatchError:
                continue


async def get_leaderboard(db: Session, class_id: UUID, limit: int = 50) -> list[LeaderboardEntry]:
    redis = get_redis()
    key = _redis_key(class_id)
    if not await redis.exists(key) or await redis.get(f"{key}:format") != "2":
        await rebuild_leaderboard_cache(db, class_id)

    raw = await redis.zrevrange(key, 0, limit - 1, withscores=True)
    entries = []
    for rank, (member, score) in enumerate(raw, start=1):
        _, user_id_str, name = member.split(":", 2)
        entries.append(
            LeaderboardEntry(user_id=UUID(user_id_str), name=name, score=round(score), rank=rank)
        )
    return entries


async def on_best_score_changed(db: Session, class_id: UUID) -> None:
    await get_redis().incr(f"{_redis_key(class_id)}:version")
    await rebuild_leaderboard_cache(db, class_id)
    await publish_event(
        class_channel(class_id),
        RealtimeEvent(
            type="leaderboard_updated",
            payload=LeaderboardUpdatedPayload(class_id=str(class_id)).model_dump(),
        ),
    )
