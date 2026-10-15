import re

from redis.asyncio import Redis

from app.rag.llm import LlmOutputError, call_groq_structured, load_prompt
from app.schemas.generation import MAX_SOURCE_NOTE_CHARS, GeneratedSourceNotes

MAX_CONTEXT_CHARS = 8000
MAX_SOURCE_PARTS = 16
MAX_REDUCTION_ROUNDS = 4


def split_source_text(content: str) -> list[str]:
    """Partition all source text into bounded pieces without dropping any characters."""
    parts = []
    while content:
        end = min(len(content), MAX_CONTEXT_CHARS)
        if end < len(content):
            sentence_ends = list(re.finditer(r"(?<=[.!?])\s+", content[:end]))
            if sentence_ends and sentence_ends[-1].end() >= MAX_CONTEXT_CHARS // 2:
                end = sentence_ends[-1].end()
            else:
                boundary = max(content.rfind("\n", 0, end), content.rfind(" ", 0, end))
                if boundary >= MAX_CONTEXT_CHARS // 2:
                    end = boundary + 1
        parts.append(content[:end])
        content = content[end:]
    return parts


async def prepare_source_context(redis: Redis, content: str) -> str:
    """Read every source part before synthesizing a bounded, source-only context."""
    if len(content) <= MAX_CONTEXT_CHARS:
        return content
    if len(content) > MAX_CONTEXT_CHARS * MAX_SOURCE_PARTS:
        raise LlmOutputError("Subbab terlalu panjang. Pisahkan menjadi subbab yang lebih kecil")
    for _ in range(MAX_REDUCTION_ROUNDS):
        parts = split_source_text(content)
        if len(parts) > MAX_SOURCE_PARTS:
            raise LlmOutputError("Subbab terlalu panjang. Pisahkan menjadi subbab yang lebih kecil")
        notes = []
        for part in parts:
            prompt = load_prompt("source_notes").format(
                context=part,
                max_notes_chars=MAX_SOURCE_NOTE_CHARS,
            )
            result = await call_groq_structured(
                redis,
                load_prompt("system_tutor"),
                prompt,
                GeneratedSourceNotes,
            )
            notes.append(result.notes)
        content = "\n\n".join(notes)
        if len(content) <= MAX_CONTEXT_CHARS:
            return content
    raise LlmOutputError(
        "Materi belum bisa diringkas dengan aman. Pisahkan subbab menjadi lebih kecil"
    )
