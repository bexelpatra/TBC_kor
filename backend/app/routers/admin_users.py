"""사용자(학생/학부모) 관리 — admin 전용."""
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import excel, schemas
from app.database import get_db
from app.deps import get_current_admin
from app.errors import bad_request, not_found
from app.models import AppUser
from app.pagination import paginate
from app.security import aes_decrypt, aes_encrypt, decrypt_name, hash_password, initial_user_password, name_hmac

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"], dependencies=[Depends(get_current_admin)])


def _to_out(u: AppUser) -> schemas.UserOut:
    return schemas.UserOut(
        id=u.id, phone_tail=u.phone_tail, name=decrypt_name(u.name_enc),
        student_number=aes_decrypt(u.student_number_enc), must_change_pw=u.must_change_pw,
    )


@router.get("", response_model=schemas.Page)
def list_users(
    phone_tail: str | None = Query(default=None),
    name: str | None = Query(default=None),
    page: int = 1, size: int = 10, db: Session = Depends(get_db),
):
    stmt = select(AppUser).where(AppUser.deleted_at.is_(None))
    if phone_tail:
        stmt = stmt.where(AppUser.phone_tail == phone_tail)
    if name:
        stmt = stmt.where(AppUser.name_hash == name_hmac(name))
    stmt = stmt.order_by(AppUser.created_at.desc())
    items, total, page, size = paginate(db, stmt, page, size)
    return schemas.Page(items=[_to_out(u).model_dump() for u in items], total=total, page=page, size=size)


@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(body: schemas.UserCreate, db: Session = Depends(get_db)):
    nh = name_hmac(body.name)
    exists = db.execute(
        select(AppUser).where(AppUser.phone_tail == body.phone_tail, AppUser.name_hash == nh, AppUser.deleted_at.is_(None))
    ).scalar_one_or_none()
    if exists:
        raise bad_request("DUPLICATE_USER", "이미 등록된 뒷번호+이름 입니다")
    from app.security import encrypt_name
    u = AppUser(
        phone_tail=body.phone_tail, name_enc=encrypt_name(body.name), name_hash=nh,
        student_number_enc=aes_encrypt(body.student_number),
        password_hash=hash_password(initial_user_password(body.student_number)),
        must_change_pw=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return _to_out(u)


@router.get("/all", response_model=list[schemas.UserOut])
def list_all_users(db: Session = Depends(get_db)):
    """페이징/필터 없이 최대 2000건 전체 조회 — 프론트엔드에서 검색/정렬/페이징 처리.

    이름은 AES 암호화 저장이라 DB에서 부분일치 검색이 불가능하므로,
    전체를 복호화해 내려준 뒤 프론트에서 검색한다.
    """
    stmt = (
        select(AppUser)
        .where(AppUser.deleted_at.is_(None))
        .order_by(AppUser.created_at.desc())
        .limit(2000)
    )
    items = db.execute(stmt).scalars().all()
    return [_to_out(u) for u in items]


@router.get("/template")
def download_template():
    data = excel.build_template()
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="user_template.xlsx"'},
    )


@router.post("/bulk", response_model=schemas.BulkResult)
def bulk_upload(file: UploadFile, db: Session = Depends(get_db)):
    from app.security import encrypt_name
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise bad_request("INVALID_FORMAT", "엑셀 .xlsx 파일만 업로드할 수 있습니다. '양식 다운로드'로 받은 파일을 사용하세요")
    raw = file.file.read()
    if not raw:
        raise bad_request("EMPTY_FILE", "빈 파일입니다. 내용이 있는 .xlsx 파일을 업로드하세요")
    try:
        rows = excel.parse_rows(raw)
    except Exception:
        raise bad_request("UNREADABLE_XLSX", "엑셀 파일을 읽을 수 없습니다. '양식 다운로드'로 받은 .xlsx 형식인지 확인하세요")
    created, skipped, errors, results = 0, [], [], []
    seen = set()  # 파일 내 중복 방지
    for r in rows:
        reason = excel.validate_row(r)
        if reason:
            errors.append({"row": r["row"], "reason": reason})
            results.append({"row": r["row"], "status": "오류", "reason": reason})
            continue
        nh = name_hmac(r["name"])
        key = (r["phone_tail"], nh)
        if key in seen:
            skipped.append({"row": r["row"], "reason": "파일 내 중복"})
            results.append({"row": r["row"], "status": "건너뜀", "reason": "파일 내 중복"})
            continue
        dup = db.execute(
            select(AppUser).where(AppUser.phone_tail == r["phone_tail"], AppUser.name_hash == nh, AppUser.deleted_at.is_(None))
        ).scalar_one_or_none()
        if dup:
            skipped.append({"row": r["row"], "reason": "기존 등록 중복"})
            results.append({"row": r["row"], "status": "건너뜀", "reason": "기존 등록 중복"})
            continue
        seen.add(key)
        db.add(AppUser(
            phone_tail=r["phone_tail"], name_enc=encrypt_name(r["name"]), name_hash=nh,
            student_number_enc=aes_encrypt(r["student_number"]),
            password_hash=hash_password(initial_user_password(r["student_number"])),
            must_change_pw=True,
        ))
        created += 1
        results.append({"row": r["row"], "status": "생성", "reason": None})
    db.commit()
    return schemas.BulkResult(created=created, skipped=skipped, errors=errors, results=results)


@router.post("/bulk/report")
def bulk_report(body: schemas.BulkReportRequest):
    data = excel.build_result_report(body.results)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="user_bulk_result.xlsx"'},
    )


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(AppUser, user_id)
    if not u or u.deleted_at is not None:
        raise not_found()
    return _to_out(u)


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, body: schemas.UserUpdate, db: Session = Depends(get_db)):
    u = db.get(AppUser, user_id)
    if not u or u.deleted_at is not None:
        raise not_found()
    if body.name is not None:
        from app.security import encrypt_name
        name = body.name.strip()
        if len(name) < 2:
            raise bad_request("INVALID_NAME", "이름은 2자 이상 입력하세요")
        nh = name_hmac(name)
        # (뒷번호, 이름) 유니크 인덱스(uq_app_user_login) 충돌을 저장 전에 차단
        dup = db.execute(
            select(AppUser).where(
                AppUser.phone_tail == u.phone_tail,
                AppUser.name_hash == nh,
                AppUser.id != u.id,
                AppUser.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if dup:
            raise bad_request("DUPLICATE_USER", "이미 등록된 뒷번호+이름 입니다")
        u.name_enc = encrypt_name(name)
        u.name_hash = nh
    if body.student_number is not None:
        u.student_number_enc = aes_encrypt(body.student_number)
    db.commit()
    db.refresh(u)
    return _to_out(u)


@router.post("/{user_id}/reset-password", response_model=schemas.UserOut)
def reset_password(user_id: int, db: Session = Depends(get_db)):
    u = db.get(AppUser, user_id)
    if not u or u.deleted_at is not None:
        raise not_found()
    u.password_hash = hash_password(initial_user_password(aes_decrypt(u.student_number_enc)))
    u.must_change_pw = True
    db.commit()
    db.refresh(u)
    return _to_out(u)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    from sqlalchemy import func
    u = db.get(AppUser, user_id)
    if not u or u.deleted_at is not None:
        raise not_found()
    u.deleted_at = func.now()
    db.commit()
