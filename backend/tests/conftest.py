import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.realtime.pubsub as pubsub
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, get_db
from app.main import app

# Tests wipe tables, so they must never run against the development database.
_dev_url = make_url(settings.database_url)
_test_url = _dev_url.set(database=f"{_dev_url.database}_test")


def _ensure_test_database() -> None:
    admin = create_engine(_dev_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.exec_driver_sql(
            "SELECT 1 FROM pg_database WHERE datname = %s", (_test_url.database,)
        ).first()
        if exists is None:
            conn.exec_driver_sql(f'CREATE DATABASE "{_test_url.database}"')
    admin.dispose()


_ensure_test_database()
engine = create_engine(_test_url)
# Worker jobs and websockets open their own sessions via SessionLocal; point them at the test DB.
SessionLocal.configure(bind=engine)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(autouse=True)
def _real_llm_mode(monkeypatch):
    """A dev .env may set LLM_MODE=mock; tests use the real path unless they opt in."""
    monkeypatch.setattr(settings, "llm_mode", "groq")
    monkeypatch.setattr(settings, "mock_llm_delay_seconds", 0)


@pytest.fixture(autouse=True)
def _fake_redis():
    pubsub._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield pubsub._redis
    pubsub._redis = None


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
