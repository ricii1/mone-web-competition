"""Development seeder: `python -m app.db.seed`.

Idempotent: does nothing if the seed teacher already exists. Chunks/embeddings are not
seeded (they need the embedding model, which only runs in the worker), so seeded
questions have no `source_chunk_id`.
"""

import asyncio
import sys

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.class_ import ClassStatus, ClassVisibility, Enrollment
from app.models.user import User, UserRole
from app.services.example_class import (
    ELEMENTARY_LEVELS,
    build_class,
    create_example_class,
    has_example_class,
)
from app.services.example_content import LESSONS
from app.services.leaderboard_service import rebuild_leaderboard_cache
from app.services.progress_service import initialize_progress_for_enrollment, record_quiz_result

SEED_PASSWORD = "password123"
TEACHER_EMAIL = "guru@petapintar.id"
STUDENTS = [
    ("Andi Pratama", "murid1@petapintar.id"),
    ("Budi Santoso", "murid2@petapintar.id"),
    ("Citra Lestari", "murid3@petapintar.id"),
    ("Dewi Anggraini", "murid4@petapintar.id"),
]

DRAFT_LEVELS = ELEMENTARY_LEVELS[:1]


def seed(db: Session) -> bool:
    if db.query(User).filter(User.email == TEACHER_EMAIL).first() is not None:
        return False

    password_hash = hash_password(SEED_PASSWORD)
    teacher = User(
        name="Bu Sari (Guru)",
        email=TEACHER_EMAIL,
        password_hash=password_hash,
        role=UserRole.teacher,
    )
    students = [
        User(name=name, email=email, password_hash=password_hash, role=UserRole.student)
        for name, email in STUDENTS
    ]
    db.add(teacher)
    db.add_all(students)
    db.flush()

    public_levels = build_class(
        db,
        teacher,
        title="IPA Kelas 4 - Siklus Air",
        description="Ayo mengenal penguapan, awan, hujan, dan cara menjaga air.",
        visibility=ClassVisibility.public,
        status=ClassStatus.published,
        levels=ELEMENTARY_LEVELS,
        approved_levels=len(ELEMENTARY_LEVELS),
    )
    for level, spec in zip(public_levels, LESSONS, strict=False):
        level.content = spec["content"]
    draft_levels = build_class(
        db,
        teacher,
        title="IPA Kelas 4 (Draft Privat)",
        description="Materi siklus air yang masih menunggu tinjauan guru.",
        visibility=ClassVisibility.private,
        status=ClassStatus.draft,
        levels=DRAFT_LEVELS,
        approved_levels=0,
    )
    draft_levels[0].content = LESSONS[0]["content"]
    create_example_class(db, teacher)

    public_class_id = public_levels[0].class_id
    for student in students:
        db.add(Enrollment(user_id=student.id, class_id=public_class_id))
    db.commit()
    for student in students:
        initialize_progress_for_enrollment(db, student.id, public_class_id)

    # Scores per student per level, applied through the real service
    # so unlock/best_score rules stay consistent.
    results = {
        0: [(0, 100), (1, 80), (2, 90), (3, 70)],
        1: [(0, 100), (1, 90)],
        2: [(0, 60), (0, 80)],
        3: [],
    }
    for student_index, scores in results.items():
        for level_index, score in scores:
            record_quiz_result(db, students[student_index].id, public_levels[level_index].id, score)

    asyncio.run(rebuild_leaderboard_cache(db, public_class_id))
    return True


def backfill_examples(db: Session) -> int:
    """Give the example class to every existing user that lacks one."""
    count = 0
    for teacher in db.query(User).all():
        if not has_example_class(db, teacher.id):
            create_example_class(db, teacher)
            count += 1
    db.commit()
    return count


def main() -> None:
    if "--examples" in sys.argv:
        with SessionLocal() as db:
            print(f"Class contoh ditambahkan untuk {backfill_examples(db)} guru.")
        return
    with SessionLocal() as db:
        if seed(db):
            print("Seed selesai.")
            print(f"  Guru : {TEACHER_EMAIL} / {SEED_PASSWORD}")
            for _, email in STUDENTS:
                print(f"  Murid: {email} / {SEED_PASSWORD}")
        else:
            print("Seed dilewati: data seed sudah ada.", file=sys.stderr)


if __name__ == "__main__":
    main()
