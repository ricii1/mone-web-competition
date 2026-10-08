from uuid import UUID

from app.db.session import SessionLocal
from app.models.class_ import Class, GenerationStatus
from app.models.level import Level, LevelChunk, LevelType
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.question import Question, QuestionStatus
from app.rag.llm import call_groq_structured, load_prompt
from app.realtime.channels import class_channel
from app.realtime.events import GenerationProgressPayload, LevelCreatedPayload, RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event
from app.schemas.generation import (
    GeneratedLevelLesson,
    GeneratedLevelSummary,
    GeneratedQuestionsOutput,
)
from app.services.level_service import (
    LEVELS_PER_BOSS,
    QUESTIONS_PER_LEVEL,
    delete_draft_levels,
    has_approved_level,
)

# About 2000 tokens of context per call: enough for a whole section (the lesson article is
# written from it) while keeping Groq token usage per level bounded.
MAX_CONTEXT_CHARS = 8000


async def _publish_stage(
    class_id: str, stage: str, current: int, total: int, error_message: str | None = None
) -> None:
    payload = GenerationProgressPayload(
        class_id=class_id,
        stage=stage,
        current=current,
        total=total,
        error_message=error_message,
    )
    await publish_event(
        class_channel(UUID(class_id)),
        RealtimeEvent(type="generation_progress", payload=payload.model_dump()),
    )


def _set_generation_state(
    db, class_id: UUID, status: GenerationStatus, error: str | None = None
) -> None:
    cls = db.get(Class, class_id)
    if cls is None:
        return
    cls.generation_status = status
    cls.generation_error = error
    db.commit()


async def _write_lesson(redis, content: str) -> GeneratedLevelLesson:
    prompt = load_prompt("lesson_level").format(context=content[:MAX_CONTEXT_CHARS])
    result: GeneratedLevelLesson = await call_groq_structured(
        redis, load_prompt("system_tutor"), prompt, GeneratedLevelLesson
    )
    return result


async def _summarize(redis, content: str) -> GeneratedLevelSummary:
    prompt = load_prompt("summarize_level").format(context=content[:MAX_CONTEXT_CHARS])
    result: GeneratedLevelSummary = await call_groq_structured(
        redis, load_prompt("system_tutor"), prompt, GeneratedLevelSummary
    )
    return result


async def _generate_questions(db, redis, level: Level, chunks: list[MaterialChunk]) -> None:
    context = "\n\n".join(c.content for c in chunks)[:MAX_CONTEXT_CHARS]
    prompt = load_prompt("generate_questions").format(
        num_questions=QUESTIONS_PER_LEVEL, context=context
    )
    result: GeneratedQuestionsOutput = await call_groq_structured(
        redis, load_prompt("system_tutor"), prompt, GeneratedQuestionsOutput
    )
    source_chunk_id = chunks[0].id if len(chunks) == 1 else None
    for q in result.questions:
        db.add(
            Question(
                level_id=level.id,
                question_text=q.question_text,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                source_chunk_id=source_chunk_id,
                status=QuestionStatus.draft,
            )
        )
    db.commit()


async def generate_levels_and_questions(ctx: dict, class_id: str) -> None:
    """Job arq: buat draft level + soal dari material yang sudah ready.

    Idempotent: refuses if any level is approved, otherwise replaces all draft levels.
    State is stored in Postgres (classes.generation_status) before events are published.
    """
    db = SessionLocal()
    redis = get_redis()
    try:
        class_id_uuid = UUID(class_id)
        if has_approved_level(db, class_id_uuid):
            raise ValueError("Class sudah punya level yang disetujui; tidak bisa digenerate ulang")
        _set_generation_state(db, class_id_uuid, GenerationStatus.generating)
        delete_draft_levels(db, class_id_uuid)

        chunks = (
            db.query(MaterialChunk)
            .join(Material, Material.id == MaterialChunk.material_id)
            .filter(
                Material.class_id == class_id_uuid, Material.vector_status == VectorStatus.ready
            )
            .order_by(Material.created_at, MaterialChunk.page_start)
            .all()
        )
        if not chunks:
            raise ValueError("Belum ada materi yang siap (vector_status=ready) untuk class ini")

        await _publish_stage(class_id, "generating_levels", 0, len(chunks))

        order_index = 0
        prev_level_id = None
        boss_group: list[MaterialChunk] = []
        boss_count = 0

        for idx, chunk in enumerate(chunks):
            lesson = await _write_lesson(redis, chunk.content)
            level = Level(
                class_id=class_id_uuid,
                prerequisite_id=prev_level_id,
                title=chunk.section_title or f"Bagian {idx + 1}",
                type=LevelType.lesson_quiz,
                order_index=order_index,
                content=lesson.content,
                summary=lesson.summary,
                key_points=lesson.key_points,
            )
            db.add(level)
            db.commit()
            db.refresh(level)
            db.add(LevelChunk(level_id=level.id, chunk_id=chunk.id))
            db.commit()

            await publish_event(
                class_channel(class_id_uuid),
                RealtimeEvent(
                    type="level_created",
                    payload=LevelCreatedPayload(
                        level_id=str(level.id),
                        class_id=class_id,
                        title=level.title,
                        order_index=level.order_index,
                    ).model_dump(),
                ),
            )
            await _publish_stage(class_id, "generating_questions", idx + 1, len(chunks))
            await _generate_questions(db, redis, level, [chunk])

            prev_level_id = level.id
            order_index += 1
            boss_group.append(chunk)

            is_last = idx == len(chunks) - 1
            if len(boss_group) >= LEVELS_PER_BOSS and not is_last:
                boss_count += 1
                boss_lesson = await _summarize(redis, "\n\n".join(c.content for c in boss_group))
                boss_level = Level(
                    class_id=class_id_uuid,
                    prerequisite_id=prev_level_id,
                    title=f"Tantangan Boss {boss_count}",
                    type=LevelType.boss,
                    order_index=order_index,
                    summary=boss_lesson.summary,
                    key_points=boss_lesson.key_points,
                )
                db.add(boss_level)
                db.commit()
                db.refresh(boss_level)
                for c in boss_group:
                    db.add(LevelChunk(level_id=boss_level.id, chunk_id=c.id))
                db.commit()

                await publish_event(
                    class_channel(class_id_uuid),
                    RealtimeEvent(
                        type="level_created",
                        payload=LevelCreatedPayload(
                            level_id=str(boss_level.id),
                            class_id=class_id,
                            title=boss_level.title,
                            order_index=boss_level.order_index,
                        ).model_dump(),
                    ),
                )
                await _generate_questions(db, redis, boss_level, boss_group)

                prev_level_id = boss_level.id
                order_index += 1
                boss_group = []

        _set_generation_state(db, class_id_uuid, GenerationStatus.done)
        await _publish_stage(class_id, "done", len(chunks), len(chunks))
    except Exception as exc:
        db.rollback()
        message = str(exc) or "Generate level gagal"
        try:
            _set_generation_state(db, UUID(class_id), GenerationStatus.failed, message)
        finally:
            await _publish_stage(class_id, "failed", 0, 0, message)
        raise
    finally:
        db.close()
