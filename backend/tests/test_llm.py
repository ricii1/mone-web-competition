import fakeredis.aioredis
import pytest
from pydantic import BaseModel

from app.rag import llm as llm_module
from app.rag.llm import LlmOutputError, call_groq_structured


class _Schema(BaseModel):
    summary: str


@pytest.fixture
def redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


async def test_call_groq_structured_parses_valid_json(monkeypatch, redis):
    monkeypatch.setattr(llm_module, "_call_groq_sync", lambda *a, **k: '{"summary": "ok"}')

    result = await call_groq_structured(redis, "system", "user", _Schema)

    assert result.summary == "ok"


async def test_call_groq_structured_retries_then_succeeds(monkeypatch, redis):
    calls = {"n": 0}

    def fake_call(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return "bukan json valid"
        return '{"summary": "berhasil setelah retry"}'

    monkeypatch.setattr(llm_module, "_call_groq_sync", fake_call)

    result = await call_groq_structured(redis, "system", "user", _Schema)

    assert result.summary == "berhasil setelah retry"
    assert calls["n"] == 2


async def test_call_groq_structured_gives_up_after_max_retries(monkeypatch, redis):
    monkeypatch.setattr(llm_module, "_call_groq_sync", lambda *a, **k: "selalu rusak")

    with pytest.raises(LlmOutputError):
        await call_groq_structured(redis, "system", "user", _Schema)


async def test_call_groq_structured_rejects_schema_mismatch(monkeypatch, redis):
    monkeypatch.setattr(llm_module, "_call_groq_sync", lambda *a, **k: '{"wrong_field": "x"}')

    with pytest.raises(LlmOutputError):
        await call_groq_structured(redis, "system", "user", _Schema)
