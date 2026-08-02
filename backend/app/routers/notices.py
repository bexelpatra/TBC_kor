"""공지 — user/admin 읽기, admin CRUD + 이미지."""
from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.config import settings
from app.database import get_db
from app.deps import get_current_admin, get_token_payload
from app.errors import bad_request, not_found
from app.models import Attachment, Notice
from app.numbering import next_serial_no
from app.pagination import paginate
from app.storage import process_image, storage

router = APIRouter(tags=["notices"])


def _images(db: Session, notice_id: int) -> list[schemas.AttachmentOut]:
    rows = db.execute(
        select(Attachment).where(
            Attachment.target_type == "notice", Attachment.target_id == notice_id, Attachment.deleted_at.is_(None)
        ).order_by(Attachment.display_order)
    ).scalars().all()
    return [schemas.AttachmentOut(id=a.id, url=storage.url(a.file_path), display_order=a.display_order, title=a.title) for a in rows]


def _out(db: Session, n: Notice) -> schemas.NoticeOut:
    return schemas.NoticeOut(
        id=n.id, notice_at=n.notice_at, serial_no=n.serial_no, admin_user_id=n.admin_user_id,
        title=n.title, content=n.content, images=_images(db, n.id),
    )


# ----- 읽기 (user/admin) -----
@router.get("/api/notices", response_model=schemas.Page)
def list_notices(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    title: str | None = Query(default=None),
    page: int = 1, size: int = 10,
    _=Depends(get_token_payload), db: Session = Depends(get_db),
):
    stmt = select(Notice).where(Notice.deleted_at.is_(None))
    if title:
        stmt = stmt.where(Notice.title.ilike(f"%{title}%"))
    if date_from:
        stmt = stmt.where(Notice.notice_at >= date_from)
    if date_to:
        stmt = stmt.where(Notice.notice_at <= date_to)
    stmt = stmt.order_by(Notice.notice_at.desc())
    items, total, page, size = paginate(db, stmt, page, size)
    return schemas.Page(items=[_out(db, n).model_dump() for n in items], total=total, page=page, size=size)


@router.get("/api/notices/{notice_id}", response_model=schemas.NoticeOut)
def get_notice(notice_id: int, _=Depends(get_token_payload), db: Session = Depends(get_db)):
    n = db.get(Notice, notice_id)
    if not n or n.deleted_at is not None:
        raise not_found()
    return _out(db, n)


# ----- CRUD (admin) -----
@router.post("/api/admin/notices", response_model=schemas.NoticeOut, status_code=201)
def create_notice(body: schemas.NoticeCreate, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    n = Notice(notice_at=body.notice_at, serial_no=next_serial_no(db), admin_user_id=admin.id, title=body.title, content=body.content)
    db.add(n)
    db.commit()
    db.refresh(n)
    return _out(db, n)


@router.put("/api/admin/notices/{notice_id}", response_model=schemas.NoticeOut)
def update_notice(notice_id: int, body: schemas.NoticeUpdate, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    n = db.get(Notice, notice_id)
    if not n or n.deleted_at is not None:
        raise not_found()
    if body.title is not None:
        n.title = body.title
    if body.content is not None:
        n.content = body.content
    db.commit()
    db.refresh(n)
    return _out(db, n)


@router.delete("/api/admin/notices/{notice_id}", status_code=204)
def delete_notice(notice_id: int, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    n = db.get(Notice, notice_id)
    if not n or n.deleted_at is not None:
        raise not_found()
    n.deleted_at = func.now()
    db.commit()


@router.post("/api/admin/notices/{notice_id}/images", response_model=list[schemas.AttachmentOut])
async def upload_notice_images(notice_id: int, files: list[UploadFile] = File(...), admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    n = db.get(Notice, notice_id)
    if not n or n.deleted_at is not None:
        raise not_found()
    existing = db.execute(
        select(func.count()).select_from(Attachment).where(
            Attachment.target_type == "notice", Attachment.target_id == notice_id, Attachment.deleted_at.is_(None)
        )
    ).scalar() or 0
    order = existing
    prefix = f"notice/{notice_id}"
    for f in files:
        data, ext = process_image(await f.read(), f.filename)
        key = storage.save(data, ext, prefix=prefix)
        db.add(Attachment(target_type="notice", target_id=notice_id, file_path=key, display_order=order))
        order += 1
    db.commit()
    return _images(db, notice_id)
