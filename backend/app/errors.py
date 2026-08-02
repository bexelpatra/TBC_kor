"""공통 에러 — 응답 형식 { "error": { "code", "message" } }."""
from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


async def api_error_handler(_: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


# 자주 쓰는 에러
def unauthorized(msg="인증이 필요합니다"):
    return APIError(401, "UNAUTHORIZED", msg)


def forbidden(msg="권한이 없습니다"):
    return APIError(403, "FORBIDDEN", msg)


def not_found(msg="대상을 찾을 수 없습니다"):
    return APIError(404, "NOT_FOUND", msg)


def bad_request(code, msg):
    return APIError(400, code, msg)
