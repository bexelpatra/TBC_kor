# API 명세 (api_spec.md)

> 작성: Architect | 다음 에이전트: Backend
> 모든 응답 에러 형식: `{ "error": { "code": "", "message": "" } }`
> 인증: `Authorization: Bearer <JWT>` (user 20분 / admin 4시간). MCP는 `X-API-Key`.
> 페이징 공통 쿼리: `?page=1&size=10|20|30`. 응답: `{ items: [...], total, page, size }`.

## 인증 (auth)

### POST /api/auth/login/user
- body: `{ "phone_tail": "1234", "name": "홍길동", "password": "123456" }`
- 200: `{ "access_token", "token_type": "bearer", "expires_in": 1200, "must_change_pw": false }`
- 401: 자격 불일치

### POST /api/auth/login/admin
- body: `{ "login_id": "teacher01", "password": "abcd1234" }`
- 200: `{ "access_token", "expires_in": 14400, "role", "level" }`

### GET /api/auth/me
- 200: `{ "actor": "user|admin", "id", "display_name", "expires_at" }` (남은 시간 표시용)

### POST /api/auth/password (최초/일반 변경)
- body: `{ "current", "new" }` — user 6자리 숫자 / admin 8자+ 영문·숫자

---

## 사용자 관리 (admin 전용) — /api/admin/users

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/admin/users` | 목록(검색·페이징) |
| POST | `/api/admin/users` | 단건 추가 (뒷번호·이름·번호 4자리) |
| GET | `/api/admin/users/{id}` | 상세 |
| PUT | `/api/admin/users/{id}` | 수정 |
| DELETE | `/api/admin/users/{id}` | 탈퇴(soft delete) |
| GET | `/api/admin/users/template` | 엑셀 양식 다운로드(헤더: 뒷번호(학부모)·이름·번호(4자리)) |
| POST | `/api/admin/users/bulk` | 엑셀 업로드 일괄 등록 |
| POST | `/api/admin/users/bulk/report` | 일괄 등록 결과 전체를 `.xlsx`로 다운로드 |

- bulk 응답: `{ "created": N, "skipped": [{row, reason:"중복"}], "errors": [{row, field, reason}], "results": [{row, status, reason}] }` (초기 비밀번호 = `00`+번호 4자리)
- bulk/report 요청: `{ "results": [...] }` (bulk 응답의 `results`를 그대로 전달) → 헤더: `행`, `상태`, `사유`

---

## 특강 (admin 작성) — /api/admin/lectures

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/admin/lectures` | 강의 마스터 생성 `{ lecture_at, subject? }` (round_no 자동 채번) |
| GET | `/api/admin/lectures` | 강의 목록(검색·페이징) |
| GET/PUT/DELETE | `/api/admin/lectures/{id}` | 상세/수정/삭제 |
| POST | `/api/admin/lectures/{id}/students` | 학생별 기록 생성 `{ user_id, title, content }` (다건 가능) |
| GET | `/api/admin/lectures/{id}/students` | 강의의 학생별 기록 목록(이름·이미지 포함) |
| PUT/DELETE | `/api/admin/lecture-users/{id}` | 학생별 기록 수정/삭제 |
| POST | `/api/admin/lecture-users/{id}/images` | 이미지 업로드(multipart, 최대 5장, 720p 재압축) |
| DELETE | `/api/admin/attachments/{id}` | 첨부 삭제 |

## 특강 (user 조회) — /api/lectures
- **모든 응답은 본인(`user_id`) 것만.** 서버에서 강제 스코핑.

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/lectures` | 본인 특강 목록. 쿼리: `date_from, date_to, title, page, size` |
| GET | `/api/lectures/{lecture_user_id}` | 본인 기록 상세(내용·이미지·본인 댓글·admin 답글). 타인 것이면 404 |

## 댓글 — /api/lectures/{lecture_user_id}/comments
| 메서드 | 경로 | 액터 | 설명 |
|---|---|---|---|
| GET | `/api/lectures/{lecture_user_id}/comments` | user | 본인 기록의 댓글·답글 목록 |
| GET | `/api/admin/lecture-users/{id}/comments` | admin | 해당 기록의 댓글·답글 목록 |
| POST | `.../comments` | user | 댓글 작성(본인 기록만) |
| PUT/DELETE | `/api/comments/{id}` | user | 본인 댓글 수정/삭제(답글 달리기 전까지) |
| POST | `/api/comments/{id}/reply` | admin | 답글(1단계) |
| GET | `/api/admin/comments/unanswered` | admin | 미답변 댓글 모아보기(인박스) |

---

## 공지 — /api/notices
| 메서드 | 경로 | 액터 | 설명 |
|---|---|---|---|
| GET | `/api/notices` | user/admin | 목록(검색·페이징) |
| GET | `/api/notices/{id}` | user/admin | 상세 |
| POST/PUT/DELETE | `/api/admin/notices[/{id}]` | admin | CRUD |
| POST | `/api/admin/notices/{id}/images` | admin | 이미지 업로드 |

---

## MCP API (관리자 전용·읽기 전용) — /api/mcp
- 인증: `X-API-Key`. 쓰기 없음.

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/mcp/lectures` | 특강 검색/조회(날짜·제목·학생) |
| GET | `/api/mcp/lectures/{id}` | 특강 상세 |
| GET | `/api/mcp/notices` | 공지 검색/조회 |
| GET | `/api/mcp/notices/{id}` | 공지 상세 |

> Backend는 구현 후 실제 성공/에러 응답 JSON 예시를 `/docs/backend/api_response_examples.md`에 작성한다.
