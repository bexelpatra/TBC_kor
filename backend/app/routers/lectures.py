"""특강 — user(학부모) 조회. 모든 응답은 본인(user_id) 것만 (절대 격리)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.deps import get_current_user
from app.errors import not_found
from app.models import Attachment, Comment, Lecture, LectureUser
from app.pagination import paginate
from app.storage import storage

router = APIRouter(prefix="/api/lectures", tags=["lectures"])


@router.get("", response_model=schemas.Page)
def my_lectures(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    title: str | None = Query(default=None),
    page: int = 1, size: int = 10,
    user=Depends(get_current_user), db: Session = Depends(get_db),
):
    # 본인 user_id로 강제 스코핑 — 다른 학부모 기록에 쿼리가 닿지 않음
    stmt = (
        select(LectureUser)
        .join(Lecture, LectureUser.lecture_id == Lecture.id)
        .where(LectureUser.app_user_id == user.id, LectureUser.deleted_at.is_(None), Lecture.deleted_at.is_(None))
    )
    if title:
        stmt = stmt.where(LectureUser.title.ilike(f"%{title}%"))
    if date_from:
        stmt = stmt.where(Lecture.lecture_at >= date_from)
    if date_to:
        stmt = stmt.where(Lecture.lecture_at <= date_to)
    stmt = stmt.order_by(Lecture.lecture_at.desc())
    items, total, page, size = paginate(db, stmt, page, size)

    out = []
    for lu in items:
        l = db.get(Lecture, lu.lecture_id)
        out.append(schemas.LectureUserOut(
            id=lu.id, lecture_id=lu.lecture_id, round_no=l.round_no, lecture_at=l.lecture_at,
            title=lu.title, content=lu.content, created_at=lu.created_at,
        ).model_dump())
    return schemas.Page(items=out, total=total, page=page, size=size)


@router.get("/{lecture_user_id}", response_model=schemas.LectureUserOut)
def my_lecture_detail(lecture_user_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lecture_user_id)
    # 타인 기록이면 존재를 숨기기 위해 404
    if not lu or lu.deleted_at is not None or lu.app_user_id != user.id:
        raise not_found()
    l = db.get(Lecture, lu.lecture_id)
    images = db.execute(
        select(Attachment).where(
            Attachment.target_type == "lecture_user", Attachment.target_id == lu.id, Attachment.deleted_at.is_(None)
        ).order_by(Attachment.display_order)
    ).scalars().all()
    return schemas.LectureUserOut(
        id=lu.id, lecture_id=lu.lecture_id, round_no=l.round_no, lecture_at=l.lecture_at,
        title=lu.title, content=lu.content, created_at=lu.created_at,
        images=[schemas.AttachmentOut(id=a.id, url=storage.url(a.file_path), display_order=a.display_order, title=a.title) for a in images],
    )
