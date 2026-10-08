from uuid import UUID

from app.db.session import SessionLocal
from app.models.level import Level, LevelChunk, LevelType
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.question import Question, QuestionStatus
from app.rag.llm import call_groq_structured, load_prompt
from app.realtime.channels import class_channel
from app.realtime.events import LevelCreatedPayload, MaterialProgressPayload, RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event
from app.schemas.generation import GeneratedLevelSummary, GeneratedQuestionsOutput
from app.services.level_service import LEVELS_PER_BOSS, QUESTIONS_PER_LEVEL

MAX_CONTEXT_CHARS = 6000


async def _publish_stage(class_id: str, stage: str, current: int, total: int) -> None:
    payload = MaterialProgressPayload(
        material_id=class_id, stage=stage, current=current, total=total
    )
    await publish_event(
        class_channel(UUID(class_id)),
        RealtimeEvent(type="material_progress", payload=payload.model_dump()),
    )


async def _summarize(redis, content: str) -> str:
    prompt = load_prompt("summarize_level").format(context=content[:MAX_CONTEXT_CHARS])
    result: GeneratedLevelSummary = await call_groq_structured(
        redis, load_prompt("system_tutor"), prompt, GeneratedLevelSummary
    )
    return result.summary


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

    ponytail: hanya berjalan sekali per class (menolak jika sudah ada level),
    upgrade path bila perlu regenerasi parsial: hapus level berstatus draft
    dahulu sebelum membuat ulang, agar retry benar-benar idempoten.
    """
    db = SessionLocal()
    redis = get_redis()
    try:
        class_id_uuid = UUID(class_id)
        if db.query(Level).filter(Level.class_id == class_id_uuid).first() is not None:
            raise ValueError("Class sudah punya level; hapus level draft dulu untuk generate ulang")

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
            summary = await _summarize(redis, chunk.content)
            level = Level(
                class_id=class_id_uuid,
                prerequisite_id=prev_level_id,
                title=chunk.section_title or f"Bagian {idx + 1}",
                type=LevelType.lesson_quiz,
                order_index=order_index,
                summary=summary,
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
                boss_summary = await _summarize(redis, "\n\n".join(c.content for c in boss_group))
                boss_level = Level(
                    class_id=class_id_uuid,
                    prerequisite_id=prev_level_id,
                    title=f"Tantangan Boss {boss_count}",
                    type=LevelType.boss,
                    order_index=order_index,
                    summary=boss_summary,
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

        await _publish_stage(class_id, "done", len(chunks), len(chunks))
    except Exception:
        await _publish_stage(class_id, "failed", 0, 0)
        raise
    finally:
        db.close()
