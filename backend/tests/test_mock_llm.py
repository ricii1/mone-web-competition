import pytest

from app.core.config import settings
from app.rag.llm import call_groq_structured, load_prompt
from app.rag.mock_llm import MockLlmError
from app.schemas.generation import GeneratedLevelSummary, GeneratedQuestionsOutput

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
