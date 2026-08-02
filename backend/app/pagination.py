"""페이징 공통 — size는 10/20/30만 허용."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

ALLOWED_SIZES = {10, 20, 30}


def normalize(page: int, size: int) -> tuple[int, int]:
    page = max(1, page)
    if size not in ALLOWED_SIZES:
        size = 10
    return page, size


def paginate(db: Session, stmt, page: int, size: int):
    """stmt(정렬 포함)에 count + limit/offset 적용. 반환: (items, total)."""
    page, size = normalize(page, size)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    items = db.execute(stmt.limit(size).offset((page - 1) * size)).scalars().all()
    return items, total, page, size
