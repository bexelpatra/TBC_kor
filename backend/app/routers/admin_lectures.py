"""특강 — admin 작성/관리 (강의 마스터 + 학생별 기록 + 이미지)."""
from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.config import settings
from app.database import get_db
from app.deps import get_current_admin
from app.errors import bad_request, not_found
from app.models import Attachment, Lecture, LectureUser
from app.numbering import next_round_no
from app.pagination import paginate
from app.storage import process_image, storage

router = APIRouter(prefix="/api/admin", tags=["admin-lectures"], dependencies=[Depends(get_current_admin)])


def _lecture_out(l: Lecture) -> schemas.LectureOut:
    return schemas.LectureOut(id=l.id, lecture_at=l.lecture_at, round_no=l.round_no, admin_user_id=l.admin_user_id, subject=l.subject)


def _images_of(db: Session, target_type: str, target_id: int) -> list[schemas.AttachmentOut]:
    rows = db.execute(
        select(Attachment).where(
            Attachment.target_type == target_type, Attachment.target_id == target_id, Attachment.deleted_at.is_(None)
        ).order_by(Attachment.display_order)
    ).scalars().all()
    return [schemas.AttachmentOut(id=a.id, url=storage.url(a.file_path), display_order=a.display_order, title=a.title) for a in rows]


# ----- 강의 마스터 -----
@router.post("/lectures", response_model=schemas.LectureOut, status_code=201)
def create_lecture(body: schemas.LectureCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    l = Lecture(lecture_at=body.lecture_at, round_no=next_round_no(db), admin_user_id=admin.id, subject=body.subject)
    db.add(l)
    db.commit()
    db.refresh(l)
    return _lecture_out(l)


@router.get("/lectures", response_model=schemas.Page)
def list_lectures(
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
    return schemas.Page(items=[_lecture_out(l).model_dump() for l in items], total=total, page=page, size=size)


@router.get("/lectures/{lecture_id}", response_model=schemas.LectureOut)
def get_lecture(lecture_id: int, db: Session = Depends(get_db)):
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found()
    return _lecture_out(l)


@router.put("/lectures/{lecture_id}", response_model=schemas.LectureOut)
def update_lecture(lecture_id: int, body: schemas.LectureCreate, db: Session = Depends(get_db)):
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found()
    l.lecture_at = body.lecture_at
    l.subject = body.subject
    db.commit()
    db.refresh(l)
    return _lecture_out(l)


@router.delete("/lectures/{lecture_id}", status_code=204)
def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found()
    l.deleted_at = func.now()
    db.commit()


# ----- 학생별 기록 -----
@router.post("/lectures/{lecture_id}/students", response_model=list[schemas.LectureUserOut], status_code=201)
def add_students(lecture_id: int, body: list[schemas.LectureUserCreate], db: Session = Depends(get_db)):
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found("강의를 찾을 수 없습니다")
    out = []
    for item in body:
        dup = db.execute(
            select(LectureUser).where(
                LectureUser.lecture_id == lecture_id, LectureUser.app_user_id == item.app_user_id, LectureUser.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
        if dup:
            raise bad_request("DUPLICATE_LECTURE_USER", f"이미 등록된 학생(app_user_id={item.app_user_id})")
        lu = LectureUser(lecture_id=lecture_id, app_user_id=item.app_user_id, title=item.title, content=item.content)
        db.add(lu)
        db.flush()
        out.append(lu)
    db.commit()
    return [
        schemas.LectureUserOut(
            id=lu.id, lecture_id=lu.lecture_id, round_no=l.round_no, lecture_at=l.lecture_at,
            title=lu.title, content=lu.content, images=_images_of(db, "lecture_user", lu.id),
            created_at=lu.created_at,
        ) for lu in out
    ]


@router.get("/lectures/{lecture_id}/students")
def list_students(lecture_id: int, db: Session = Depends(get_db)):
    from app.models import AppUser
    from app.security import decrypt_name
    l = db.get(Lecture, lecture_id)
    if not l or l.deleted_at is not None:
        raise not_found()
    rows = db.execute(
        select(LectureUser).where(LectureUser.lecture_id == lecture_id, LectureUser.deleted_at.is_(None)).order_by(LectureUser.id)
    ).scalars().all()
    out = []
    for lu in rows:
        u = db.get(AppUser, lu.app_user_id)
        out.append({
            "id": lu.id, "app_user_id": lu.app_user_id,
            "student_name": decrypt_name(u.name_enc) if u else "",
            "phone_tail": u.phone_tail if u else "",
            "title": lu.title, "content": lu.content,
            "created_at": lu.created_at.isoformat(),
            "images": [a.model_dump() for a in _images_of(db, "lecture_user", lu.id)],
        })
    return out


@router.put("/lecture-users/{lu_id}", response_model=schemas.LectureUserOut)
def update_lecture_user(lu_id: int, body: schemas.LectureUserUpdate, db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lu_id)
    if not lu or lu.deleted_at is not None:
        raise not_found()
    if body.title is not None:
        lu.title = body.title
    if body.content is not None:
        lu.content = body.content
    db.commit()
    db.refresh(lu)
    l = db.get(Lecture, lu.lecture_id)
    return schemas.LectureUserOut(
        id=lu.id, lecture_id=lu.lecture_id, round_no=l.round_no, lecture_at=l.lecture_at,
        title=lu.title, content=lu.content, images=_images_of(db, "lecture_user", lu.id),
        created_at=lu.created_at,
    )


@router.delete("/lecture-users/{lu_id}", status_code=204)
def delete_lecture_user(lu_id: int, db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lu_id)
    if not lu or lu.deleted_at is not None:
        raise not_found()
    lu.deleted_at = func.now()
    db.commit()


# ----- 이미지 -----
@router.post("/lecture-users/{lu_id}/images", response_model=list[schemas.AttachmentOut])
async def upload_images(lu_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lu_id)
    if not lu or lu.deleted_at is not None:
        raise not_found()
    existing = db.execute(
        select(func.count()).select_from(Attachment).where(
            Attachment.target_type == "lecture_user", Attachment.target_id == lu_id, Attachment.deleted_at.is_(None)
        )
    ).scalar() or 0
    order = existing
    prefix = f"lecture/{lu.lecture_id}/{lu.app_user_id}"
    for f in files:
        data, ext = process_image(await f.read(), f.filename)
        key = storage.save(data, ext, prefix=prefix)
        db.add(Attachment(target_type="lecture_user", target_id=lu_id, file_path=key, display_order=order))
        order += 1
    db.commit()
    return _images_of(db, "lecture_user", lu_id)


@router.delete("/attachments/{att_id}", status_code=204)
def delete_attachment(att_id: int, db: Session = Depends(get_db)):
    a = db.get(Attachment, att_id)
    if not a or a.deleted_at is not None:
        raise not_found()
    a.deleted_at = func.now()
    db.commit()
