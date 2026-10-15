import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_placeholder_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql://app:a-long-example-test-password@db/app",
            redis_url="redis://localhost",
            jwt_secret="change-me-in-production",
        )


def test_production_accepts_long_secret():
    config = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql://app:a-long-example-test-password@db/app",
        redis_url="redis://localhost",
        jwt_secret="a" * 64,
    )
    assert config.app_env == "production"


@pytest.mark.parametrize("password", ["edumap", "petapintar"])
def test_production_rejects_example_database_password(password):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            database_url=f"postgresql://app:{password}@db/app",
            redis_url="redis://localhost",
            jwt_secret="a" * 64,
        )
