"""회차/일련번호 자동 채번 — advisory lock으로 직렬화 후 MAX+1.

soft delete된 행의 번호도 MAX 계산에 포함(번호 재사용 안 함).
"""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Lecture, Notice

# 테이블별 advisory lock 키 (임의 고정 정수)
_LOCK_LECTURE = 1001
_LOCK_NOTICE = 1002


def next_round_no(db: Session) -> int:
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LOCK_LECTURE})
    cur = db.execute(select(func.max(Lecture.round_no))).scalar()
    return (cur or 0) + 1


def next_serial_no(db: Session) -> int:
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LOCK_NOTICE})
    cur = db.execute(select(func.max(Notice.serial_no))).scalar()
    return (cur or 0) + 1
