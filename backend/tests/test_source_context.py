from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest

from app.rag import context
from app.rag.llm import LlmOutputError
from app.schemas.generation import GeneratedSourceNotes


@pytest.mark.parametrize(
    "source", ["kata " * 3000, "x" * 20001, "awal\n" + "kata " * 3000 + "AKHIR"]
)
def test_source_partition_preserves_every_character(source):
    parts = context.split_source_text(source)
    assert "".join(parts) == source
    assert all(0 < len(part) <= context.MAX_CONTEXT_CHARS for part in parts)


async def test_small_context_uses_no_extra_llm_call(monkeypatch):
    call = AsyncMock()
    monkeypatch.setattr(context, "call_groq_structured", call)
    assert await context.prepare_source_context(None, "Materi pendek") == "Materi pendek"
    call.assert_not_awaited()


async def test_long_context_reads_tail_and_all_parts(monkeypatch):
    source = "AWAL. " + "Materi sumber tentang tumbuhan. " * 550 + "AKHIR_SUMBER."
    captured = []

    async def extract(redis, system, prompt, schema):
        part = prompt.split("Konteks materi:\n", 1)[1].split("\n\nKembalikan HANYA JSON", 1)[0]
        captured.append(part)
        notes = "Catatan hanya dari sumber."
        if "AWAL" in part:
            notes += " AWAL."
        if "AKHIR_SUMBER" in part:
            notes += " AKHIR_SUMBER."
        return GeneratedSourceNotes(notes=notes)

    monkeypatch.setattr(context, "call_groq_structured", extract)
    result = await context.prepare_source_context(None, source)
    assert "".join(captured) == source
    assert "AWAL" in result and "AKHIR_SUMBER" in result
    assert len(result) <= context.MAX_CONTEXT_CHARS


async def test_reduction_rounds_have_a_bounded_number_of_calls(monkeypatch):
    call = AsyncMock(return_value=GeneratedSourceNotes(notes="catatan " * 249))
    monkeypatch.setattr(context, "call_groq_structured", call)
    source = "x" * (context.MAX_CONTEXT_CHARS * context.MAX_SOURCE_PARTS)
    result = await context.prepare_source_context(None, source)
    assert len(result) <= context.MAX_CONTEXT_CHARS
    assert context.MAX_SOURCE_PARTS < call.await_count <= 24


async def test_oversized_source_fails_before_llm_instead_of_truncating(monkeypatch):
    call = AsyncMock()
    monkeypatch.setattr(context, "call_groq_structured", call)
    with pytest.raises(LlmOutputError, match="Subbab terlalu panjang"):
        await context.prepare_source_context(
            None, "x" * (context.MAX_CONTEXT_CHARS * context.MAX_SOURCE_PARTS + 1)
        )
    call.assert_not_awaited()


async def test_mock_mode_retains_end_of_long_source(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_mode", "mock")
    monkeypatch.setattr(settings, "mock_llm_delay_seconds", 0)
    source = "Fakta awal tanaman memerlukan air. " + "Daun tumbuhan berwarna hijau. " * 400
    source += "Fakta terakhir tanaman dapat memiliki bunga."
    result = await context.prepare_source_context(
        fakeredis.aioredis.FakeRedis(decode_responses=True), source
    )
    assert "Fakta awal" in result
    assert "Fakta terakhir" in result


def test_source_partition_prefers_complete_sentences():
    source = "Akar tumbuhan menyerap air dari tanah. " * 600
    parts = context.split_source_text(source)
    assert "".join(parts) == source
    assert all(part.rstrip().endswith(".") for part in parts)
