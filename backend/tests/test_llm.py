import fakeredis.aioredis
import httpx
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


def _fake_post(payload: dict, status_code: int = 200):
    captured: dict = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, body=json)
        return httpx.Response(status_code, json=payload, request=httpx.Request("POST", url))

    return fake_post, captured


def test_openai_call_uses_gateway_and_strips_think(monkeypatch):
    payload = {"choices": [{"message": {"content": '<think>mikir</think>{"summary": "ok"}'}}]}
    fake_post, captured = _fake_post(payload)
    monkeypatch.setattr(llm_module.settings, "llm_mode", "openai")
    monkeypatch.setattr(llm_module.settings, "api_key_litellm", "kunci")
    monkeypatch.setattr(llm_module.httpx, "post", fake_post)

    raw = llm_module._call_groq_sync("system", "user")

    assert raw == '{"summary": "ok"}'
    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"]["Authorization"] == "Bearer kunci"
    assert captured["body"]["model"] == llm_module.settings.llm_model


def test_openai_call_exposes_status_for_rate_limit(monkeypatch):
    fake_post, _ = _fake_post({"error": "slow down"}, status_code=429)
    monkeypatch.setattr(llm_module.settings, "llm_mode", "openai")
    monkeypatch.setattr(llm_module.httpx, "post", fake_post)

    with pytest.raises(llm_module.LlmHttpError) as exc_info:
        llm_module._call_groq_sync("system", "user")

    assert exc_info.value.status_code == 429
