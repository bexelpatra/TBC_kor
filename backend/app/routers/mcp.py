"""MCP API — 관리자 API 키 인증, 읽기 전용 (특강/공지 조회)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.deps import require_mcp_admin
from app.errors import not_found
from app.models import Lecture, LectureUser, Notice
from app.pagination import paginate

router = APIRouter(prefix="/api/mcp", tags=["mcp"], dependencies=[Depends(require_mcp_admin)])


@router.get("/lectures", response_model=schemas.Page)
def mcp_lectures(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    subject: str | None = Query(default=None),
    page: int = 1, size: int = 10, db: Session = Depends(get_db),
):
    stmt = select(Lecture).where(Lecture.deleted_at.is_(None))
    if date_from:
        stmt = stmt.where(Lecture.lecture_at >= date_from)
    if date_to:
        stmt = stmt.where(Lecture.lecture_at <= date_to)
    if subject:
        stmt = stmt.where(Lecture.subject.ilike(f"%{subject}%"))
    stmt = stmt.order_by(Lecture.lecture_at.desc())
    items, total, page, size = paginate(db, stmt, page, size)
    out = [{"id": l.id, "lecture_at": l.lecture_at.isoformat(), "round_no": l.round_no, "subject": l.subject} for l in items]
    return schemas.Page(items=out, total=total, page=page, size=size)


@router.get("/lectures/{lecture_id}")
def mcp_lecture_detail(lecture_id: int, db: Session = Depends(get_db)):
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found()
    students = db.execute(
        select(LectureUser).where(LectureUser.lecture_id == lecture_id, LectureUser.deleted_at.is_(None))
    ).scalars().all()
    return {
        "id": l.id, "lecture_at": l.lecture_at.isoformat(), "round_no": l.round_no, "subject": l.subject,
        "students": [{"lecture_user_id": s.id, "app_user_id": s.app_user_id, "title": s.title, "content": s.content} for s in students],
    }


@router.get("/notices", response_model=schemas.Page)
def mcp_notices(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    title: str | None = Query(default=None),
    page: int = 1, size: int = 10, db: Session = Depends(get_db),
):
    stmt = select(Notice).where(Notice.deleted_at.is_(None))
    if date_from:
        stmt = stmt.where(Notice.notice_at >= date_from)
    if date_to:
        stmt = stmt.where(Notice.notice_at <= date_to)
    if title:
        stmt = stmt.where(Notice.title.ilike(f"%{title}%"))
    stmt = stmt.order_by(Notice.notice_at.desc())
    items, total, page, size = paginate(db, stmt, page, size)
    out = [{"id": n.id, "notice_at": n.notice_at.isoformat(), "serial_no": n.serial_no, "title": n.title, "content": n.content} for n in items]
    return schemas.Page(items=out, total=total, page=page, size=size)


@router.get("/notices/{notice_id}")
def mcp_notice_detail(notice_id: int, db: Session = Depends(get_db)):
    n = db.get(Notice, notice_id)
    if not n or n.deleted_at is not None:
        raise not_found()
    return {"id": n.id, "notice_at": n.notice_at.isoformat(), "serial_no": n.serial_no, "title": n.title, "content": n.content}
