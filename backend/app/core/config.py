from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    worker_max_jobs: int = 2

    jwt_secret: str
    jwt_expires_minutes: int = 1440
    jwt_algorithm: str = "HS256"

    groq_api_key: str = ""
    groq_model: str = ""

    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384

    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 20

    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
