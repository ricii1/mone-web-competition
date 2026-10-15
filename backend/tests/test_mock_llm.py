import pytest

from app.core.config import settings
from app.rag.llm import call_groq_structured, load_prompt
from app.rag.mock_llm import MockLlmError
from app.schemas.generation import (
    GeneratedLevelLesson,
    GeneratedLevelSummary,
    GeneratedQuestionsOutput,
)

CONTEXT = (
    "Mitokondria adalah organel yang menghasilkan energi bagi sel. "
    "Ribosom berfungsi untuk membuat protein di dalam sel hidup. "
    "Nukleus menyimpan materi genetik yang mengatur aktivitas sel."
)


@pytest.fixture
def mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "mock")


async def test_mock_summary_comes_from_context(mock_mode):
    prompt = load_prompt("summarize_level").format(context=CONTEXT)
    result = await call_groq_structured(None, "sys", prompt, GeneratedLevelSummary)
    assert "Mitokondria" in result.summary
    assert set(result.summary.split()) <= set(CONTEXT.split())


def _bare(text: str) -> set[str]:
    return {w.strip(".,;:").lower() for w in text.split()}


async def test_mock_key_points_are_grounded_in_context(mock_mode):
    prompt = load_prompt("summarize_level").format(context=CONTEXT)
    result = await call_groq_structured(None, "sys", prompt, GeneratedLevelSummary)
    assert 3 <= len(result.key_points) <= 6
    for point in result.key_points:
        assert _bare(point) <= _bare(CONTEXT)


async def test_mock_key_points_prefer_later_sentences(mock_mode):
    context = CONTEXT + (
        " Membran sel mengatur zat yang keluar masuk sel. "
        "Lisosom mencerna sisa zat di dalam sel hidup."
    )
    prompt = load_prompt("summarize_level").format(context=context)
    result = await call_groq_structured(None, "sys", prompt, GeneratedLevelSummary)
    assert result.key_points[0].startswith("Membran sel")
    for point in result.key_points:
        assert _bare(point) <= _bare(context)


async def test_mock_summary_rejects_context_without_enough_key_points(mock_mode):
    prompt = load_prompt("summarize_level").format(
        context="Mitokondria adalah organel yang menghasilkan energi bagi sel."
    )
    with pytest.raises(MockLlmError):
        await call_groq_structured(None, "sys", prompt, GeneratedLevelSummary)


async def test_mock_questions_are_valid_and_grounded(mock_mode):
    prompt = load_prompt("generate_questions").format(num_questions=5, context=CONTEXT)
    result = await call_groq_structured(None, "sys", prompt, GeneratedQuestionsOutput)
    assert len(result.questions) == 5
    for q in result.questions:
        assert len(q.options) == 4
        assert len(set(q.options)) == 4
        assert q.correct_answer in q.options
        assert q.correct_answer.lower() in CONTEXT.lower()
        assert "_____" in q.question_text


async def test_mock_rejects_context_too_short(mock_mode):
    prompt = load_prompt("generate_questions").format(num_questions=5, context="Pendek.")
    with pytest.raises(MockLlmError):
        await call_groq_structured(None, "sys", prompt, GeneratedQuestionsOutput)


async def test_mock_questions_remain_unique_for_repeated_sentences(mock_mode):
    context = (
        "Panas matahari membuat air laut menguap menjadi uap air. "
        "Uap air kemudian naik ke langit dan menjadi dingin. "
    ) * 4
    prompt = load_prompt("generate_questions").format(num_questions=5, context=context)
    result = await call_groq_structured(None, "sys", prompt, GeneratedQuestionsOutput)
    assert len(result.questions) == 5
    assert len({" ".join(q.question_text.split()).casefold() for q in result.questions}) == 5
    for question in result.questions:
        assert question.correct_answer in question.options
        assert question.correct_answer.casefold() in context.casefold()
        assert len({option.casefold() for option in question.options}) == 4


async def test_mock_explains_when_source_cannot_supply_enough_unique_questions(mock_mode):
    context = "Air baik untuk kita dan tubuh manusia. " * 5
    prompt = load_prompt("generate_questions").format(num_questions=5, context=context)
    with pytest.raises(MockLlmError, match="5 soal berbeda"):
        await call_groq_structured(None, "sys", prompt, GeneratedQuestionsOutput)


LESSON_CONTEXT = (
    "Siklus Air\n"
    "Air di bumi selalu berputar dari tempat yang satu ke tempat yang lain. "
    "Panas matahari membuat air laut menguap menjadi uap air. "
    "Uap air naik ke langit dan menjadi dingin. Uap air yang dingin berubah menjadi awan. "
    "Awan yang berat menjatuhkan hujan ke bumi. Hujan mengisi sungai dan danau.\n\n"
    "Tahap siklus air:\n"
    "- Penguapan\n"
    "- Pengembunan\n"
    "- Hujan\n"
)


async def test_mock_lesson_content_is_grounded_and_reflowed(mock_mode):
    prompt = load_prompt("lesson_level").format(context=LESSON_CONTEXT)
    result = await call_groq_structured(None, "sys", prompt, GeneratedLevelLesson)
    blocks = result.content.split("\n\n")
    assert blocks[0] == "### Siklus Air"
    # 6 prose sentences re-flowed into paragraphs of up to 3 sentences, then the bullet list.
    assert len(blocks[1].split(". ")) == 3
    assert blocks[-1] == "- Penguapan\n- Pengembunan\n- Hujan"
    context_words = _bare(LESSON_CONTEXT)
    for word in _bare(result.content.replace("###", "").replace("- ", "")):
        assert word in context_words
    assert 3 <= len(result.key_points) <= 6


async def test_mock_lesson_without_heading_uses_generic_heading(mock_mode):
    prompt = load_prompt("lesson_level").format(
        context=" ".join([LESSON_CONTEXT.split("\n", 1)[1]])
    )
    result = await call_groq_structured(None, "sys", prompt, GeneratedLevelLesson)
    assert result.content.startswith("### Penjelasan Materi")


async def test_mock_lesson_rejects_too_short_context(mock_mode):
    prompt = load_prompt("lesson_level").format(
        context="Mitokondria adalah organel yang menghasilkan energi bagi sel."
    )
    with pytest.raises(MockLlmError):
        await call_groq_structured(None, "sys", prompt, GeneratedLevelLesson)
