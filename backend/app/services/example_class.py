"""Reference ("example") class given to every new teacher so the dashboard is never empty.

It is an elementary-school class (IPA Kelas 4 - Siklus Air) showing the level map, lesson
articles, summaries, sources and the question review flow: the first level is approved, the
rest are drafts waiting for the teacher. Content is hand-written (no real PDF). The material
and its chunks are fake: embeddings are zero vectors, which is fine because the example class
can never be generated or published, so nothing ever retrieves from them.

`BIOLOGY_LEVELS` is only demo data for the seeded public student/leaderboard class.
"""

import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_invite_code
from app.models.class_ import Class, ClassStatus, ClassVisibility
from app.models.level import Level, LevelChunk, LevelStatus, LevelType
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.question import Question, QuestionStatus
from app.models.user import User
from app.services.example_content import BOSS_LEVEL, LESSONS, MATERIAL_FILE_NAME

EXAMPLE_TITLE = "Contoh: IPA Kelas 4 - Siklus Air"
EXAMPLE_DESCRIPTION = (
    "Class contoh sebagai gambaran hasil akhir: peta level, materi bacaan, rangkuman, sumber, "
    "dan soal. Level pertama sudah disetujui, sisanya masih draft untuk Anda review. "
    "Class ini tidak bisa dipublish; buat class baru untuk materi Anda sendiri."
)

# (title, type, summary, key_points, [(question, options, correct index, explanation)])
BIOLOGY_LEVELS = [
    (
        "Pengenalan Sel",
        LevelType.lesson_quiz,
        "Sel adalah unit struktural dan fungsional terkecil makhluk hidup. Sel prokariotik "
        "tidak memiliki membran inti, sedangkan sel eukariotik memilikinya.",
        [
            "Sel adalah unit struktural dan fungsional terkecil makhluk hidup.",
            "Sel prokariotik tidak memiliki membran inti.",
            "Sel eukariotik memiliki membran inti.",
        ],
        [
            (
                "Apa unit struktural dan fungsional terkecil makhluk hidup?",
                ["Jaringan", "Sel", "Organ", "Molekul"],
                1,
                "Sel adalah unit terkecil kehidupan.",
            ),
            (
                "Ciri utama sel prokariotik adalah...",
                [
                    "Memiliki inti sel",
                    "Tidak memiliki membran inti",
                    "Memiliki mitokondria",
                    "Selalu multiseluler",
                ],
                1,
                "Prokariotik tidak punya membran inti.",
            ),
            (
                "Contoh organisme prokariotik adalah...",
                ["Bakteri", "Jamur", "Amoeba", "Paku"],
                0,
                "Bakteri adalah prokariotik.",
            ),
            (
                "Siapa yang pertama kali mengamati sel pada irisan gabus?",
                ["Robert Hooke", "Louis Pasteur", "Mendel", "Darwin"],
                0,
                "Robert Hooke mengamati sel gabus pada 1665.",
            ),
            (
                "Sel eukariotik memiliki...",
                ["Hanya DNA bebas", "Membran inti", "Tidak ada organel", "Hanya satu ribosom"],
                1,
                "Eukariotik punya inti sel dengan membran.",
            ),
        ],
    ),
    (
        "Organel Sel",
        LevelType.lesson_quiz,
        "Organel menjalankan fungsi khusus: mitokondria menghasilkan energi, ribosom membuat "
        "protein, dan kloroplas melakukan fotosintesis pada sel tumbuhan.",
        [
            "Organel menjalankan fungsi khusus di dalam sel.",
            "Mitokondria menghasilkan energi.",
            "Ribosom membuat protein.",
            "Kloroplas melakukan fotosintesis pada sel tumbuhan.",
        ],
        [
            (
                "Organel penghasil energi (ATP) adalah...",
                ["Ribosom", "Mitokondria", "Lisosom", "Vakuola"],
                1,
                "Mitokondria: respirasi sel.",
            ),
            (
                "Tempat sintesis protein adalah...",
                ["Ribosom", "Nukleus", "Kloroplas", "Golgi"],
                0,
                "Ribosom merakit protein.",
            ),
            (
                "Organel fotosintesis pada tumbuhan adalah...",
                ["Mitokondria", "Kloroplas", "Lisosom", "Sentriol"],
                1,
                "Kloroplas berklorofil.",
            ),
            (
                "Organel pencernaan intrasel adalah...",
                ["Lisosom", "Ribosom", "Nukleolus", "Kloroplas"],
                0,
                "Lisosom berisi enzim.",
            ),
            (
                "Pusat pengatur aktivitas sel adalah...",
                ["Vakuola", "Nukleus", "Membran sel", "Sitoplasma"],
                1,
                "Nukleus menyimpan DNA.",
            ),
        ],
    ),
    (
        "Membran dan Transpor",
        LevelType.lesson_quiz,
        "Membran sel bersifat selektif permeabel. Difusi dan osmosis berjalan tanpa energi, "
        "sedangkan transpor aktif memerlukan energi.",
        [
            "Membran sel bersifat selektif permeabel.",
            "Difusi berjalan tanpa energi.",
            "Osmosis berjalan tanpa energi.",
            "Transpor aktif memerlukan energi.",
        ],
        [
            (
                "Perpindahan zat dari konsentrasi tinggi ke rendah disebut...",
                ["Difusi", "Transpor aktif", "Endositosis", "Eksositosis"],
                0,
                "Difusi mengikuti gradien konsentrasi.",
            ),
            (
                "Osmosis adalah perpindahan...",
                ["Ion", "Air", "Protein", "Glukosa saja"],
                1,
                "Osmosis: difusi air.",
            ),
            (
                "Transpor aktif memerlukan...",
                ["Energi (ATP)", "Cahaya", "Tekanan udara", "Tidak ada"],
                0,
                "Melawan gradien.",
            ),
            (
                "Sifat membran sel adalah...",
                ["Impermeabel", "Selektif permeabel", "Permeabel penuh", "Kaku"],
                1,
                "Hanya zat tertentu yang lewat.",
            ),
            (
                "Larutan hipertonik membuat sel hewan...",
                ["Mengembang", "Mengerut", "Tetap", "Membelah"],
                1,
                "Air keluar dari sel.",
            ),
        ],
    ),
    (
        "Boss: Biologi Sel",
        LevelType.boss,
        "Gabungan materi pengenalan sel, organel, dan transpor membran.",
        [
            "Sel prokariotik tidak punya membran inti, sel eukariotik punya.",
            "Mitokondria menghasilkan energi, ribosom membuat protein, kloroplas berfotosintesis.",
            "Difusi dan osmosis tanpa energi, transpor aktif memerlukan energi.",
        ],
        [
            (
                "Organel yang disebut 'pembangkit tenaga' sel adalah...",
                ["Mitokondria", "Ribosom", "Lisosom", "Golgi"],
                0,
                "Mitokondria menghasilkan ATP.",
            ),
            (
                "Sel tanpa membran inti disebut...",
                ["Eukariotik", "Prokariotik", "Hewan", "Tumbuhan"],
                1,
                "Prokariotik.",
            ),
            (
                "Air berpindah melalui membran dengan cara...",
                ["Osmosis", "Fotosintesis", "Fisi", "Mitosis"],
                0,
                "Osmosis.",
            ),
            (
                "Fotosintesis terjadi di...",
                ["Kloroplas", "Mitokondria", "Nukleus", "Lisosom"],
                0,
                "Kloroplas.",
            ),
            (
                "Pengiriman zat melawan gradien konsentrasi disebut...",
                ["Difusi", "Osmosis", "Transpor aktif", "Difusi terfasilitasi"],
                2,
                "Transpor aktif memakai ATP.",
            ),
        ],
    ),
]


def build_class(
    db: Session,
    teacher: User,
    *,
    title: str,
    description: str,
    visibility: ClassVisibility,
    status: ClassStatus,
    levels: list,
    approved_levels: int,
    is_example: bool = False,
) -> list[Level]:
    """Create a class with a linear level chain; the first `approved_levels` are approved."""
    cls = Class(
        teacher_id=teacher.id,
        title=title,
        description=description,
        visibility=visibility,
        invite_code=generate_invite_code() if visibility == ClassVisibility.private else None,
        status=status,
        is_example=is_example,
    )
    db.add(cls)
    db.flush()

    created: list[Level] = []
    for index, (level_title, level_type, summary, key_points, questions) in enumerate(levels):
        approved = index < approved_levels
        level = Level(
            class_id=cls.id,
            prerequisite_id=created[-1].id if created else None,
            title=level_title,
            type=level_type,
            order_index=index,
            summary=summary,
            key_points=key_points,
            status=LevelStatus.approved if approved else LevelStatus.draft,
        )
        db.add(level)
        db.flush()
        for text, options, correct, explanation in questions:
            db.add(
                Question(
                    level_id=level.id,
                    question_text=text,
                    options=options,
                    correct_answer=options[correct],
                    explanation=explanation,
                    status=QuestionStatus.approved if approved else QuestionStatus.draft,
                )
            )
        created.append(level)
    db.flush()
    return created


EXAMPLE_FILE_PATH = "example/contoh-ipa-siklus-air.pdf"


def _plain_text(markdown: str) -> str:
    """Strip the Markdown subset (headings, bold, bullets) to plain text for chunk content."""
    text = re.sub(r"^#+\s*", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    return text.replace("**", "")


def populate_example_class(db: Session, cls: Class) -> list[Level]:
    """Fill an (empty) class with the SD example: fake material, 3 lessons and a boss level.

    Also sets the class title/description, so it works for new and existing example classes.
    """
    cls.title = EXAMPLE_TITLE
    cls.description = EXAMPLE_DESCRIPTION
    material = Material(
        class_id=cls.id,
        file_name=MATERIAL_FILE_NAME,
        file_path=EXAMPLE_FILE_PATH,
        vector_status=VectorStatus.ready,
    )
    db.add(material)
    db.flush()

    levels: list[Level] = []
    lesson_chunks: list[MaterialChunk] = []

    def add_level(spec: dict, level_type: LevelType, content: str | None, approved: bool) -> Level:
        level = Level(
            class_id=cls.id,
            prerequisite_id=levels[-1].id if levels else None,
            title=spec["title"],
            type=level_type,
            order_index=len(levels),
            content=content,
            summary=spec["summary"],
            key_points=spec["key_points"],
            status=LevelStatus.approved if approved else LevelStatus.draft,
        )
        db.add(level)
        db.flush()
        levels.append(level)
        return level

    def add_questions(level: Level, spec: dict, chunk: MaterialChunk | None) -> None:
        for text, options, correct, explanation in spec["questions"]:
            db.add(
                Question(
                    level_id=level.id,
                    question_text=text,
                    options=options,
                    correct_answer=options[correct],
                    explanation=explanation,
                    source_chunk_id=chunk.id if chunk else None,
                    status=QuestionStatus.approved
                    if level.status == LevelStatus.approved
                    else QuestionStatus.draft,
                )
            )

    for index, spec in enumerate(LESSONS):
        page_start, page_end = spec["pages"]
        chunk = MaterialChunk(
            material_id=material.id,
            class_id=cls.id,
            section_title=spec["title"],
            content=_plain_text(spec["content"]),
            page_start=page_start,
            page_end=page_end,
            embedding=[0.0] * settings.embedding_dim,
        )
        db.add(chunk)
        db.flush()
        lesson_chunks.append(chunk)
        level = add_level(spec, LevelType.lesson_quiz, spec["content"], approved=index == 0)
        db.add(LevelChunk(level_id=level.id, chunk_id=chunk.id))
        add_questions(level, spec, chunk)

    boss = add_level(BOSS_LEVEL, LevelType.boss, None, approved=False)
    for chunk in lesson_chunks:
        db.add(LevelChunk(level_id=boss.id, chunk_id=chunk.id))
    add_questions(boss, BOSS_LEVEL, None)
    db.flush()
    return levels


def create_example_class(db: Session, teacher: User) -> Class:
    cls = Class(
        teacher_id=teacher.id,
        title=EXAMPLE_TITLE,
        description=EXAMPLE_DESCRIPTION,
        visibility=ClassVisibility.private,
        invite_code=generate_invite_code(),
        status=ClassStatus.draft,
        is_example=True,
    )
    db.add(cls)
    db.flush()
    populate_example_class(db, cls)
    return cls


def has_example_class(db: Session, teacher_id) -> bool:
    return (
        db.query(Class.id)
        .filter(Class.teacher_id == teacher_id, Class.is_example.is_(True))
        .first()
        is not None
    )
