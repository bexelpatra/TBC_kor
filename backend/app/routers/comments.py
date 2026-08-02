"""댓글 — user 작성/수정/삭제(자기 기록), admin 답글(1단계)·미답변 인박스."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.config import settings
from app.database import get_db
from app.deps import get_current_admin, get_current_user
from app.errors import bad_request, forbidden, not_found
from app.models import Comment, Lecture, LectureUser


def require_comments_enabled():
    """기능 플래그가 꺼져 있으면 모든 댓글 엔드포인트를 차단."""
    if not settings.comments_enabled:
        raise forbidden("댓글 기능이 비활성화되어 있습니다")


router = APIRouter(tags=["comments"], dependencies=[Depends(require_comments_enabled)])


def _out(c: Comment) -> schemas.CommentOut:
    return schemas.CommentOut(
        id=c.id, lecture_user_id=c.lecture_user_id, app_user_id=c.app_user_id, admin_user_id=c.admin_user_id,
        content=c.content, parent_id=c.parent_id, created_at=c.created_at,
    )


def _has_reply(db: Session, comment_id: int) -> bool:
    n = db.execute(
        select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id, Comment.deleted_at.is_(None))
    ).scalar() or 0
    return n > 0


def _list_for_lecture_user(db: Session, lecture_user_id: int) -> list[schemas.CommentOut]:
    rows = db.execute(
        select(Comment).where(Comment.lecture_user_id == lecture_user_id, Comment.deleted_at.is_(None)).order_by(Comment.created_at.asc())
    ).scalars().all()
    return [_out(c) for c in rows]


# ----- user -----
@router.get("/api/lectures/{lecture_user_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(lecture_user_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lecture_user_id)
    if not lu or lu.deleted_at is not None or lu.app_user_id != user.id:
        raise not_found()
    return _list_for_lecture_user(db, lecture_user_id)


@router.post("/api/lectures/{lecture_user_id}/comments", response_model=schemas.CommentOut, status_code=201)
def add_comment(lecture_user_id: int, body: schemas.CommentCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lecture_user_id)
    if not lu or lu.deleted_at is not None or lu.app_user_id != user.id:
        raise not_found()
    c = Comment(lecture_user_id=lecture_user_id, app_user_id=user.id, content=body.content)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c)


@router.put("/api/comments/{comment_id}", response_model=schemas.CommentOut)
def edit_comment(comment_id: int, body: schemas.CommentCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(Comment, comment_id)
    if not c or c.deleted_at is not None:
        raise not_found()
    if c.app_user_id is None or c.app_user_id != user.id:
        raise forbidden("본인 댓글만 수정할 수 있습니다")
    if _has_reply(db, comment_id):
        raise bad_request("REPLY_EXISTS", "답글이 달린 댓글은 수정할 수 없습니다")
    c.content = body.content
    db.commit()
    db.refresh(c)
    return _out(c)


@router.delete("/api/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(Comment, comment_id)
    if not c or c.deleted_at is not None:
        raise not_found()
    if c.app_user_id is None or c.app_user_id != user.id:
        raise forbidden("본인 댓글만 삭제할 수 있습니다")
    if _has_reply(db, comment_id):
        raise bad_request("REPLY_EXISTS", "답글이 달린 댓글은 삭제할 수 없습니다")
    c.deleted_at = func.now()
    db.commit()


# ----- admin -----
@router.post("/api/comments/{comment_id}/reply", response_model=schemas.CommentOut, status_code=201)
def reply_comment(comment_id: int, body: schemas.CommentCreate, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    parent = db.get(Comment, comment_id)
    if not parent or parent.deleted_at is not None:
        raise not_found()
    if parent.parent_id is not None:
        raise bad_request("NOT_TOP_LEVEL", "답글은 1단계만 허용됩니다")
    c = Comment(lecture_user_id=parent.lecture_user_id, admin_user_id=admin.id, content=body.content, parent_id=comment_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c)


@router.get("/api/admin/lecture-users/{lu_id}/comments", response_model=list[schemas.CommentOut])
def admin_list_comments(lu_id: int, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    lu = db.get(LectureUser, lu_id)
    if not lu or lu.deleted_at is not None:
        raise not_found()
    return _list_for_lecture_user(db, lu_id)


@router.get("/api/admin/comments/unanswered", response_model=schemas.Page)
def unanswered(page: int = 1, size: int = 10, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    from app.pagination import paginate
    reply = select(Comment.parent_id).where(Comment.parent_id.is_not(None), Comment.deleted_at.is_(None))
    stmt = (
        select(Comment)
        .where(
            Comment.app_user_id.is_not(None),
            Comment.parent_id.is_(None),
            Comment.deleted_at.is_(None),
            Comment.id.not_in(reply),
        )
        .order_by(Comment.created_at.asc())
    )
    items, total, page, size = paginate(db, stmt, page, size)
    return schemas.Page(items=[_out(c).model_dump() for c in items], total=total, page=page, size=size)
