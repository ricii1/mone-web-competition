import asyncio
import json
import time
from pathlib import Path
from typing import TypeVar

from groq import Groq
from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

from app.core.config import settings
from app.rag.mock_llm import mock_structured

PROMPTS_DIR = Path(__file__).parent / "prompts"
GROQ_MAX_CALLS_PER_MINUTE = 30
MAX_JSON_RETRIES = 2
MAX_RATE_LIMIT_RETRIES = 4

T = TypeVar("T", bound=BaseModel)

_client: Groq | None = None


class LlmOutputError(Exception):
    pass


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


async def _acquire_rate_limit_slot(redis: Redis) -> None:
    """Batasi panggilan Groq global per menit memakai counter di Redis."""
    minute_bucket = int(time.time() // 60)
    key = f"groq:calls:{minute_bucket}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > GROQ_MAX_CALLS_PER_MINUTE:
        await asyncio.sleep(60 - (time.time() % 60))


def _call_groq_sync(system_prompt: str, user_prompt: str) -> str:
    response = get_groq_client().chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""


async def call_groq_with_backoff(redis: Redis, system_prompt: str, user_prompt: str) -> str:
    await _acquire_rate_limit_slot(redis)

    delay = 1.0
    for attempt in range(MAX_RATE_LIMIT_RETRIES):
        try:
            return await asyncio.to_thread(_call_groq_sync, system_prompt, user_prompt)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            is_rate_limited = status_code == 429
            if not is_rate_limited or attempt == MAX_RATE_LIMIT_RETRIES - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2
    raise LlmOutputError("Groq tidak merespons setelah retry")


async def call_groq_structured(
    redis: Redis, system_prompt: str, user_prompt: str, schema: type[T]
) -> T:
    """Panggil Groq, validasi JSON dengan Pydantic, retry maksimal 2 kali jika gagal parse."""
    if settings.llm_mode == "mock":
        return await mock_structured(user_prompt, schema)

    last_error: Exception | None = None
    current_user_prompt = user_prompt

    for attempt in range(MAX_JSON_RETRIES + 1):
        raw = await call_groq_with_backoff(redis, system_prompt, current_user_prompt)
        try:
            return schema.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            current_user_prompt = (
                f"{user_prompt}\n\nOutput sebelumnya tidak valid ({exc}). "
                "Kembalikan HANYA JSON yang sesuai skema, tanpa teks tambahan."
            )

    raise LlmOutputError(f"Gagal memvalidasi output LLM setelah retry: {last_error}")
