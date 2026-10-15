"""Offline stand-in for Groq (`LLM_MODE=mock`) so the whole generate flow can be demoed/tested
without an API key. Output is built ONLY from the context passed in the prompt (cloze questions
and lead-sentence summaries), keeping the "answers come from the teacher's material" rule."""

import asyncio
import random
import re
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import settings
from app.schemas.generation import (
    MAX_SOURCE_NOTE_CHARS,
    MIN_CONTENT_CHARS,
    GeneratedLevelLesson,
    GeneratedLevelSummary,
    GeneratedQuestionsOutput,
    GeneratedSourceNotes,
)

T = TypeVar("T", bound=BaseModel)

CONTEXT_MARKER = "Konteks materi:\n"
MIN_SENTENCE_WORDS = 6
MIN_TARGET_LENGTH = 5
SUMMARY_SENTENCES = 3
MAX_KEY_POINTS = 4
MIN_KEY_POINTS = 3
MAX_KEY_POINT_WORDS = 14
MIN_CLAUSE_WORDS = 3
SENTENCES_PER_PARAGRAPH = 3
MAX_HEADING_WORDS = 8
GENERIC_HEADING = "Penjelasan Materi"
BULLET_RE = re.compile(r"^\s*(?:[-*\u2022\u25cf\u25aa]|\d+[.)])\s+(.*\S)\s*$")
FILLER_OPTIONS = ["tidak disebutkan dalam materi", "semua jawaban benar", "tidak ada jawaban benar"]


class MockLlmError(Exception):
    pass


def _extract_context(user_prompt: str) -> str:
    _, _, rest = user_prompt.partition(CONTEXT_MARKER)
    # Everything after the marker up to the JSON-schema instructions.
    context, _, _ = rest.partition("\n\nKembalikan HANYA JSON")
    return context.strip()


def _sentences(context: str) -> list[str]:
    flat = re.sub(r"\s+", " ", context)
    parts = re.split(r"(?<=[.!?])\s+", flat)
    return [p.strip() for p in parts if len(p.split()) >= MIN_SENTENCE_WORDS]


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", text) if len(w) >= MIN_TARGET_LENGTH]


def _shorten(text: str) -> str:
    words = text.split()
    if len(words) > MAX_KEY_POINT_WORDS:
        text = " ".join(words[:MAX_KEY_POINT_WORDS])
    return text.rstrip(" ,;:.!?") + "."


def _key_points(sentences: list[str]) -> list[str]:
    """Key points reuse (shortened) context text only: later sentences first, then clauses."""
    rest = sentences[SUMMARY_SENTENCES:]
    clauses = [
        clause.strip()
        for sentence in sentences
        for clause in re.split(r"[,;:]\s+", sentence)
        if len(clause.split()) >= MIN_CLAUSE_WORDS
    ]
    points: list[str] = []
    for candidate in [*rest, *clauses, *sentences]:
        point = _shorten(candidate)
        if point not in points:
            points.append(point)
        if len(points) >= MAX_KEY_POINTS:
            break
    if len(points) < MIN_KEY_POINTS:
        raise MockLlmError("Konteks tidak cukup untuk membuat poin penting")
    return points


def _summary(context: str) -> GeneratedLevelSummary:
    sentences = _sentences(context)
    if not sentences:
        raise MockLlmError("Konteks terlalu pendek untuk dirangkum")
    return GeneratedLevelSummary(
        summary=" ".join(sentences[:SUMMARY_SENTENCES]), key_points=_key_points(sentences)
    )


def _split_sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", flat) if p.strip()]


def _article(context: str) -> str:
    """Re-flow the context into Markdown (heading, ~3-sentence paragraphs, bullet lists).

    Only text already in the context is used; nothing is added except a generic heading.
    """
    lines = [line.rstrip() for line in context.splitlines()]
    heading = GENERIC_HEADING
    first_index = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first_index is not None:
        first = lines[first_index].strip()
        if (
            len(first.split()) <= MAX_HEADING_WORDS
            and not first.endswith((".", "!", "?", ":"))
            and not BULLET_RE.match(first)
        ):
            heading = first.lstrip("#").strip() or GENERIC_HEADING
            lines = lines[first_index + 1 :]

    blocks: list[str] = [f"### {heading}"]
    prose: list[str] = []
    bullets: list[str] = []

    def flush_prose() -> None:
        sentences = _split_sentences(" ".join(prose))
        for start in range(0, len(sentences), SENTENCES_PER_PARAGRAPH):
            blocks.append(" ".join(sentences[start : start + SENTENCES_PER_PARAGRAPH]))
        prose.clear()

    def flush_bullets() -> None:
        if bullets:
            blocks.append("\n".join(f"- {item}" for item in bullets))
            bullets.clear()

    for line in lines:
        match = BULLET_RE.match(line)
        if match:
            flush_prose()
            bullets.append(match.group(1))
        elif line.strip():
            flush_bullets()
            prose.append(line.strip())
        else:
            flush_prose()
            flush_bullets()
    flush_prose()
    flush_bullets()
    return "\n\n".join(blocks)


def _lesson(context: str) -> GeneratedLevelLesson:
    article = _article(context)
    if len(article) < MIN_CONTENT_CHARS:
        raise MockLlmError("Konteks terlalu pendek untuk dibuat materi")
    base = _summary(context)
    return GeneratedLevelLesson(content=article, summary=base.summary, key_points=base.key_points)


def _questions(context: str, num_questions: int) -> GeneratedQuestionsOutput:
    sentences = _sentences(context)
    if not sentences:
        raise MockLlmError("Konteks terlalu pendek untuk dibuatkan soal")
    pool = sorted({w.lower() for w in _words(context)})

    questions = []
    for index in range(num_questions):
        sentence = sentences[index % len(sentences)]
        candidates = _words(sentence)
        if not candidates:
            continue
        # Different question per pass over the same sentence: rotate the blanked word.
        target = sorted(candidates, key=len, reverse=True)[
            (index // len(sentences)) % len(candidates)
        ]
        rng = random.Random(f"{sentence}:{index}")
        in_sentence = {w.lower() for w in _words(sentence)}
        # Prefer words that are not visible in the question itself, so the blank is not guessable.
        distractors = [w for w in pool if w not in in_sentence] or [
            w for w in pool if w != target.lower()
        ]
        rng.shuffle(distractors)
        options = [target] + distractors[:3]
        for filler in FILLER_OPTIONS:
            if len(options) >= 4:
                break
            options.append(filler)
        rng.shuffle(options)
        blanked = re.sub(rf"\b{re.escape(target)}\b", "_____", sentence, count=1)
        questions.append(
            {
                "question_text": f"Lengkapi kalimat berikut sesuai materi: {blanked}",
                "options": options,
                "correct_answer": target,
                "explanation": f'Sesuai materi: "{sentence}"',
            }
        )
    if not questions:
        raise MockLlmError("Konteks tidak cukup untuk membuat soal")
    return GeneratedQuestionsOutput.model_validate({"questions": questions})


def _source_notes(context: str) -> GeneratedSourceNotes:
    if len(context) <= MAX_SOURCE_NOTE_CHARS:
        return GeneratedSourceNotes(notes=context)
    sentences = _split_sentences(context)
    chosen: set[int] = set()
    length = 0
    order = [0, len(sentences) - 1, len(sentences) // 2, *range(len(sentences))]
    for index in dict.fromkeys(order):
        sentence = sentences[index]
        if length + len(sentence) + 1 <= MAX_SOURCE_NOTE_CHARS:
            chosen.add(index)
            length += len(sentence) + 1
    notes = "\n".join(sentences[index] for index in sorted(chosen))
    if not notes:
        # Offline demo fallback for one oversized sentence; excerpts remain source text.
        width = MAX_SOURCE_NOTE_CHARS // 3 - 2
        middle = len(context) // 2
        notes = "\n".join((context[:width], context[middle : middle + width], context[-width:]))
    return GeneratedSourceNotes(notes=notes)


async def mock_structured(user_prompt: str, schema: type[T]) -> T:
    await asyncio.sleep(settings.mock_llm_delay_seconds)
    context = _extract_context(user_prompt)
    if schema is GeneratedSourceNotes:
        return _source_notes(context)  # type: ignore[return-value]
    if schema is GeneratedLevelLesson:
        return _lesson(context)  # type: ignore[return-value]
    if schema is GeneratedLevelSummary:
        return _summary(context)  # type: ignore[return-value]
    if schema is GeneratedQuestionsOutput:
        match = re.search(r"Buat (\d+) soal", user_prompt)
        return _questions(context, int(match.group(1)) if match else 5)  # type: ignore[return-value]
    raise MockLlmError(f"Mock LLM tidak mendukung skema {schema.__name__}")
