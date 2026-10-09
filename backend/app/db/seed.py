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
from app.models.level import LevelType
from app.models.user import User, UserRole
from app.services.example_class import (
    BIOLOGY_LEVELS,
    build_class,
    create_example_class,
    has_example_class,
)
from app.services.leaderboard_service import rebuild_leaderboard_cache
from app.services.progress_service import initialize_progress_for_enrollment, record_quiz_result

SEED_PASSWORD = "password123"
TEACHER_EMAIL = "guru@edumap.id"
STUDENTS = [
    ("Andi Pratama", "murid1@edumap.id"),
    ("Budi Santoso", "murid2@edumap.id"),
    ("Citra Lestari", "murid3@edumap.id"),
    ("Dewi Anggraini", "murid4@edumap.id"),
]

DRAFT_LEVELS = [
    (
        "Hukum Newton",
        LevelType.lesson_quiz,
        "Hukum I Newton: benda diam tetap diam kecuali ada gaya luar.",
        [
            "Benda diam cenderung tetap diam.",
            "Perubahan gerak hanya terjadi bila ada gaya luar.",
            "Sifat ini disebut inersia (kelembaman).",
        ],
        [
            (
                "Hukum I Newton disebut juga hukum...",
                ["Inersia", "Aksi-reaksi", "Gravitasi", "Kekekalan energi"],
                0,
                "Hukum kelembaman.",
            ),
        ],
    ),
]


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

    biology = build_class(
        db,
        teacher,
        title="Biologi Sel Kelas XI",
        description="Dasar-dasar biologi sel: organel dan transpor.",
        visibility=ClassVisibility.public,
        status=ClassStatus.published,
        levels=BIOLOGY_LEVELS,
        approved_levels=len(BIOLOGY_LEVELS),
    )
    build_class(
        db,
        teacher,
        title="Fisika Dasar (Draft Privat)",
        description="Class privat yang belum dipublish.",
        visibility=ClassVisibility.private,
        status=ClassStatus.draft,
        levels=DRAFT_LEVELS,
        approved_levels=0,
    )
    create_example_class(db, teacher)

    biology_class_id = biology[0].class_id
    for student in students:
        db.add(Enrollment(user_id=student.id, class_id=biology_class_id))
    db.commit()
    for student in students:
        initialize_progress_for_enrollment(db, student.id, biology_class_id)

    # Scores per student per level (index into `biology`), applied through the real service
    # so unlock/best_score rules stay consistent.
    results = {
        0: [(0, 100), (1, 80), (2, 90), (3, 70)],
        1: [(0, 100), (1, 90)],
        2: [(0, 60), (0, 80)],
        3: [],
    }
    for student_index, scores in results.items():
        for level_index, score in scores:
            record_quiz_result(db, students[student_index].id, biology[level_index].id, score)

    asyncio.run(rebuild_leaderboard_cache(db, biology_class_id))
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
