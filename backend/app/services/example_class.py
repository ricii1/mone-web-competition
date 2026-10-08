"""Reference ("example") class given to every new teacher so the dashboard is never empty.

It shows the level map, summaries and the question review flow: the first level is approved,
the rest are drafts waiting for the teacher. Content is hand-written (no PDF/embeddings), so
questions have no `source_chunk_id`.
"""

from sqlalchemy.orm import Session

from app.core.security import generate_invite_code
from app.models.class_ import Class, ClassStatus, ClassVisibility
from app.models.level import Level, LevelStatus, LevelType
from app.models.question import Question, QuestionStatus
from app.models.user import User

EXAMPLE_TITLE = "Contoh: Biologi Sel Kelas XI"
EXAMPLE_DESCRIPTION = (
    "Class contoh sebagai gambaran hasil akhir: peta level, ringkasan, dan soal. "
    "Level pertama sudah disetujui, sisanya masih draft untuk Anda review. "
    "Class ini tidak bisa dipublish; buat class baru untuk materi Anda sendiri."
)

# (title, type, summary, [(question, options, correct index, explanation)])
BIOLOGY_LEVELS = [
    (
        "Pengenalan Sel",
        LevelType.lesson_quiz,
        "Sel adalah unit struktural dan fungsional terkecil makhluk hidup. Sel prokariotik "
        "tidak memiliki membran inti, sedangkan sel eukariotik memilikinya.",
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
    for index, (level_title, level_type, summary, questions) in enumerate(levels):
        approved = index < approved_levels
        level = Level(
            class_id=cls.id,
            prerequisite_id=created[-1].id if created else None,
            title=level_title,
            type=level_type,
            order_index=index,
            summary=summary,
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


def create_example_class(db: Session, teacher: User) -> None:
    build_class(
        db,
        teacher,
        title=EXAMPLE_TITLE,
        description=EXAMPLE_DESCRIPTION,
        visibility=ClassVisibility.private,
        status=ClassStatus.draft,
        levels=BIOLOGY_LEVELS,
        approved_levels=1,
        is_example=True,
    )


def has_example_class(db: Session, teacher_id) -> bool:
    return (
        db.query(Class.id)
        .filter(Class.teacher_id == teacher_id, Class.is_example.is_(True))
        .first()
        is not None
    )
