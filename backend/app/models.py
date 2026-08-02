"""SQLAlchemy 모델 — schema.md / V001__init.sql 와 일치."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimestampMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AppUser(TimestampMixin, Base):
    __tablename__ = "app_user"
    phone_tail: Mapped[str] = mapped_column(String(4))
    name_enc: Mapped[bytes] = mapped_column(LargeBinary)
    name_hash: Mapped[str] = mapped_column(String(64))
    student_number_enc: Mapped[bytes] = mapped_column(LargeBinary)
    password_hash: Mapped[str] = mapped_column(Text)
    must_change_pw: Mapped[bool] = mapped_column(default=True, server_default="true")


class Admin(TimestampMixin, Base):
    __tablename__ = "admin_user"
    login_id: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(10))
    level: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    api_key_hash: Mapped[str | None] = mapped_column(Text, nullable=True)


class Lecture(TimestampMixin, Base):
    __tablename__ = "lecture"
    lecture_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    round_no: Mapped[int] = mapped_column(BigInteger)
    admin_user_id: Mapped[int] = mapped_column(BigInteger)
    subject: Mapped[str | None] = mapped_column(String(100), nullable=True)


class LectureUser(TimestampMixin, Base):
    __tablename__ = "lecture_user"
    lecture_id: Mapped[int] = mapped_column(BigInteger)
    app_user_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)


class Attachment(TimestampMixin, Base):
    __tablename__ = "attachment"
    target_type: Mapped[str] = mapped_column(String(20))  # 'lecture_user' | 'notice' | 'comment'
    target_id: Mapped[int] = mapped_column(BigInteger)
    file_path: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Comment(TimestampMixin, Base):
    __tablename__ = "comment"
    lecture_user_id: Mapped[int] = mapped_column(BigInteger)
    app_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    admin_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Notice(TimestampMixin, Base):
    __tablename__ = "notice"
    notice_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    serial_no: Mapped[int] = mapped_column(BigInteger)
    admin_user_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
