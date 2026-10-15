import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from app.models.level import Level, LevelChunk, LevelType
from app.models.material import MaterialChunk
from tests.test_worker_generate import _setup


def test_order_backfill_preserves_existing_lesson_and_source_links(db):
    cls = _setup(db, n_chunks=3)
    chunks = (
        db.query(MaterialChunk).filter_by(class_id=cls.id).order_by(MaterialChunk.page_start).all()
    )
    level = Level(
        class_id=cls.id,
        title="Materi guru",
        type=LevelType.lesson_quiz,
        order_index=0,
        content="Artikel yang sudah ditulis guru",
    )
    db.add(level)
    db.flush()
    db.add(LevelChunk(level_id=level.id, chunk_id=chunks[0].id))
    db.commit()
    path = Path(__file__).parents[1] / "alembic/versions/0009_material_chunk_order.py"
    spec = importlib.util.spec_from_file_location("chunk_order_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    connection = db.connection()
    migration.op = Operations(MigrationContext.configure(connection))
    try:
        migration.downgrade()
        migration.upgrade()
        rows = connection.execute(
            text(
                "SELECT page_start, order_index FROM material_chunks "
                "WHERE class_id = :class_id ORDER BY page_start"
            ),
            {"class_id": cls.id},
        ).all()
        assert rows == [(0, 0), (1, 1), (2, 2)]
        db.expire_all()
        assert db.query(LevelChunk).filter_by(level_id=level.id).one().chunk_id == chunks[0].id
        assert db.get(Level, level.id).content == "Artikel yang sudah ditulis guru"
    finally:
        db.rollback()
