from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.level import LevelChunk
from app.models.material import MaterialChunk
from app.rag.embedding import embed_query

DEFAULT_TOP_K = 5


def retrieve_chunks(
    db: Session, class_id: UUID, query: str, top_k: int = DEFAULT_TOP_K
) -> list[MaterialChunk]:
    query_vector = embed_query(query)
    stmt = (
        select(MaterialChunk)
        .where(MaterialChunk.class_id == class_id)
        .order_by(MaterialChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    return list(db.scalars(stmt))


def retrieve_chunks_for_level(
    db: Session, class_id: UUID, level_id: UUID, query: str, top_k: int = DEFAULT_TOP_K
) -> list[MaterialChunk]:
    query_vector = embed_query(query)
    stmt = (
        select(MaterialChunk)
        .join(LevelChunk, LevelChunk.chunk_id == MaterialChunk.id)
        .where(LevelChunk.level_id == level_id, MaterialChunk.class_id == class_id)
        .order_by(MaterialChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    return list(db.scalars(stmt))
