"""Pydantic 요청/응답 스키마."""
from datetime import datetime

from pydantic import BaseModel, Field

# ----- 공통 -----
class Page(BaseModel):
    items: list
    total: int
    page: int
    size: int


# ----- 인증 -----
class UserLogin(BaseModel):
    phone_tail: str = Field(pattern=r"^\d{4}$")
    name: str = Field(min_length=1, max_length=20)
    password: str


class AdminLogin(BaseModel):
    login_id: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime


class UserTokenOut(TokenOut):
    must_change_pw: bool


class AdminTokenOut(TokenOut):
    role: str
    level: int


class MeOut(BaseModel):
    actor: str
    id: int
    display_name: str
    expires_at: datetime


class PasswordChange(BaseModel):
    current: str
    new: str


# ----- 사용자(학생) 관리 -----
class UserCreate(BaseModel):
    phone_tail: str = Field(pattern=r"^\d{4}$")
    name: str = Field(min_length=1, max_length=20)
    student_number: str = Field(pattern=r"^\d{4}$")


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=20)
    student_number: str | None = Field(default=None, pattern=r"^\d{4}$")


class UserOut(BaseModel):
    id: int
    phone_tail: str
    name: str
    student_number: str
    must_change_pw: bool


class BulkResult(BaseModel):
    created: int
    skipped: list[dict]
    errors: list[dict]
    results: list[dict]


class BulkReportRequest(BaseModel):
    results: list[dict]


# ----- 특강 -----
class LectureCreate(BaseModel):
    lecture_at: datetime
    subject: str | None = None


class LectureOut(BaseModel):
    id: int
    lecture_at: datetime
    round_no: int
    admin_user_id: int
    subject: str | None


class LectureUserCreate(BaseModel):
    app_user_id: int
    title: str = Field(max_length=200)
    content: str | None = None


class LectureUserUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None


class AttachmentOut(BaseModel):
    id: int
    url: str
    display_order: int
    title: str | None


class LectureUserOut(BaseModel):
    id: int
    lecture_id: int
    round_no: int
    lecture_at: datetime
    title: str
    content: str | None
    images: list[AttachmentOut] = []
    created_at: datetime


# ----- 댓글 -----
class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: int
    lecture_user_id: int
    app_user_id: int | None
    admin_user_id: int | None
    content: str
    parent_id: int | None
    created_at: datetime


# ----- 공지 -----
class NoticeCreate(BaseModel):
    notice_at: datetime
    title: str = Field(max_length=200)
    content: str | None = None


class NoticeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None


class NoticeOut(BaseModel):
    id: int
    notice_at: datetime
    serial_no: int
    admin_user_id: int
    title: str
    content: str | None
    images: list[AttachmentOut] = []
