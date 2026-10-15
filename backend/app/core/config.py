from urllib.parse import unquote, urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_env: str = "development"
    database_url: str
    redis_url: str
    worker_max_jobs: int = 2

    jwt_secret: str
    jwt_expires_minutes: int = 1440
    jwt_algorithm: str = "HS256"

    groq_api_key: str = ""
    groq_model: str = ""
    # OpenAI-compatible gateway (LLM_MODE=openai), e.g. LiteLLM at ITS Senopati.
    llm_base_url: str = "https://senopati.its.ac.id/llm-gateway/v1"
    llm_model: str = "qwen3:14b"
    api_key_litellm: str = ""
    llm_timeout_seconds: float = 180.0
    # "groq" / "openai" call a real API; "mock" answers offline from the prompt context (demo/dev).
    llm_mode: str = "groq"
    mock_llm_delay_seconds: float = 0.8

    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384

    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 20

    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if len(self.jwt_secret.encode()) < 32 or "change-me" in self.jwt_secret.lower():
                raise ValueError("Production requires a random JWT_SECRET of at least 32 bytes")
            password = unquote(urlsplit(self.database_url).password or "")
            if not password or password.casefold() in {
                "edumap",
                "password",
                "postgres",
                "changeme",
            }:
                raise ValueError("Production requires a database password other than examples")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
