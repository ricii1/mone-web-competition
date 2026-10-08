from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_invite_code
from app.models.class_ import Class, ClassStatus, ClassVisibility, Enrollment
from app.models.user import User
from app.schemas.class_ import ClassCreateRequest
from app.services.progress_service import initialize_progress_for_enrollment


def create_class(db: Session, teacher: User, body: ClassCreateRequest) -> Class:
    cls = Class(
        teacher_id=teacher.id,
        title=body.title,
        description=body.description,
        visibility=body.visibility,
        invite_code=generate_invite_code() if body.visibility == ClassVisibility.private else None,
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


def get_class_or_404(db: Session, class_id: UUID) -> Class:
    cls = db.get(Class, class_id)
    if cls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class tidak ditemukan")
    return cls


def require_owner(cls: Class, teacher: User) -> None:
    if cls.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bukan pemilik class ini")


def list_public_classes(db: Session) -> list[Class]:
    return (
        db.query(Class)
        .filter(Class.visibility == ClassVisibility.public, Class.status == ClassStatus.published)
        .all()
    )


def join_class(db: Session, student: User, class_id: UUID, invite_code: str | None) -> Enrollment:
    cls = get_class_or_404(db, class_id)
    if cls.status != ClassStatus.published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Class belum dipublikasikan"
        )
    if cls.visibility == ClassVisibility.private and cls.invite_code != invite_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kode undangan salah")

    existing = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == student.id, Enrollment.class_id == class_id)
        .first()
    )
    if existing is not None:
        return existing

    enrollment = Enrollment(user_id=student.id, class_id=class_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    initialize_progress_for_enrollment(db, student.id, class_id)
    return enrollment


def list_owned_classes(db: Session, teacher_id: UUID) -> list[Class]:
    return db.query(Class).filter(Class.teacher_id == teacher_id).all()


def list_enrolled_classes(db: Session, student_id: UUID) -> list[Class]:
    return (
        db.query(Class)
        .join(Enrollment, Enrollment.class_id == Class.id)
        .filter(Enrollment.user_id == student_id)
        .all()
    )


def is_enrolled(db: Session, student_id: UUID, class_id: UUID) -> bool:
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == student_id, Enrollment.class_id == class_id)
        .first()
        is not None
    )
