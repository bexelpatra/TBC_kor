"""FastAPI 앱 진입점."""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.errors import APIError, api_error_handler
from app.routers import admin_lectures, admin_users, auth, comments, lectures, mcp, notices

logger = logging.getLogger("app")

app = FastAPI(title="BRAIN_CORE_KOR — 학원 특강 기록 공유")


# 예기치 못한 예외도 항상 JSON 본문 + CORS 헤더를 갖도록 처리.
# (기본 500 응답은 CORS 헤더가 없어 브라우저에서 "Failed to fetch"로만 보임)
@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("처리되지 않은 서버 오류: %s %s", request.method, request.url.path)
        resp = JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL", "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도하세요"}},
        )
        origin = request.headers.get("origin")
        if origin and origin in settings.cors_origin_list:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Vary"] = "Origin"
        return resp


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIError, api_error_handler)

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(admin_lectures.router)
app.include_router(lectures.router)
app.include_router(comments.router)
app.include_router(notices.router)
app.include_router(mcp.router)

# 로컬 저장 이미지 정적 서빙 (S3 이관 시 제거)
if settings.storage_backend == "local":
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    app.mount(settings.public_base_url, StaticFiles(directory=settings.storage_dir), name="files")


@app.get("/health")
def health():
    return {"status": "ok"}
