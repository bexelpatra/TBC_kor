# API 응답 예시 (api_response_examples.md)

> 작성: Backend | 다음 에이전트: Frontend
> 아래는 실제 구동 스모크 테스트에서 관찰된 응답이다. Frontend는 **가정 대신 이 형식**을 기준으로 구현한다.
> 공통 에러 형식: `{ "error": { "code", "message" } }`

## 인증

### POST /api/auth/login/admin → 200
```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 14400,
  "expires_at": "2026-06-01T09:45:04Z", "role": "관리자", "level": 10 }
```

### POST /api/auth/login/user → 200
```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 1200,
  "expires_at": "2026-06-01T05:45:04Z", "must_change_pw": true }
```
- 로그인 실패 → 401 `{ "error": { "code": "UNAUTHORIZED", "message": "로그인 정보가 일치하지 않습니다" } }`

### GET /api/auth/me → 200
```json
{ "actor": "user", "id": 1, "display_name": "홍길동", "expires_at": "2026-06-01T05:45:04Z" }
```
- `expires_at`로 **남은 로그인 시간** 카운트다운 표시.

### POST /api/auth/password → 200 `{ "ok": true }`
- user 새 비번 6자리 숫자 아님 → 400 `WEAK_PASSWORD`. admin은 영문·숫자 8자+.

## 사용자 관리 (admin)

### POST /api/admin/users → 201 / GET /{id} / 목록 items[]
```json
{ "id": 1, "phone_tail": "1234", "name": "홍길동", "student_number": "0503", "must_change_pw": true }
```
- 중복 → 400 `DUPLICATE_USER`.
- 목록: `{ "items": [UserOut...], "total": 3, "page": 1, "size": 10 }`

### PUT /api/admin/users/{id} → 200 (UserOut)
```json
{ "name": "홍길동" }
```
- `name`/`student_number` 모두 선택. 이름은 2~20자(앞뒤 공백 제거) → 미달 시 400 `INVALID_NAME`, 스키마 단계 미달은 422.
- 같은 `phone_tail`에 동일 이름이 이미 있으면 400 `DUPLICATE_USER` (유니크 인덱스 `uq_app_user_login` 사전 검사).
- 이름 변경 시 `name_enc`·`name_hash`가 함께 갱신되어 **학부모 로그인 이름도 즉시 바뀝니다.**

### POST /api/admin/users/bulk → 200
```json
{ "created": 2,
  "skipped": [ {"row": 4, "reason": "기존 등록 중복"}, {"row": 5, "reason": "파일 내 중복"} ],
  "errors":  [ {"row": 6, "reason": "뒷번호는 숫자 4자리"}, {"row": 7, "reason": "번호는 숫자 4자리"} ],
  "results": [
    {"row": 2, "status": "생성", "reason": null},
    {"row": 3, "status": "생성", "reason": null},
    {"row": 4, "status": "건너뜀", "reason": "기존 등록 중복"},
    {"row": 5, "status": "건너뜀", "reason": "파일 내 중복"},
    {"row": 6, "status": "오류", "reason": "뒷번호는 숫자 4자리"},
    {"row": 7, "status": "오류", "reason": "번호는 숫자 4자리"}
  ] }
```
- GET /api/admin/users/template → `.xlsx` 다운로드(헤더: `뒷번호(학부모)`, `이름`, `번호(4자리)`). 뒷번호·번호 컬럼은 텍스트 서식.
- POST /api/admin/users/bulk/report → `{ "results": [...] }` (위 `results` 그대로 전달) → `.xlsx` 다운로드(헤더: `행`, `상태`, `사유`). 행별 처리 결과 전체 리포트.
- 초기 비밀번호 = `00`+번호 4자리.

## 특강

### POST /api/admin/lectures → 201 (회차 자동)
```json
{ "id": 1, "lecture_at": "2026-05-20T10:00:00Z", "round_no": 1, "admin_id": 1, "subject": "5월 모의고사 해설" }
```

### POST /api/admin/lectures/{id}/students → 201 (body는 배열)
```json
[ { "id": 1, "lecture_id": 1, "round_no": 1, "lecture_at": "2026-05-20T10:00:00Z",
    "title": "홍길동 특강 피드백", "content": "홍길동 학생 내용", "images": [] } ]
```

### GET /api/lectures (user, 본인 것만) → 200
```json
{ "items": [ { "id": 1, "lecture_id": 1, "round_no": 1, "lecture_at": "2026-05-20T10:00:00Z",
    "title": "홍길동 특강 피드백", "content": "홍길동 학생 내용", "images": [] } ],
  "total": 1, "page": 1, "size": 10 }
```
- 쿼리: `date_from, date_to, title, page, size(10|20|30)`.

### GET /api/lectures/{lecture_user_id} (user) → 200 / 타인·없음 → 404
```json
{ "id": 1, "lecture_id": 1, "round_no": 1, "lecture_at": "2026-05-20T10:00:00Z",
  "title": "홍길동 특강 피드백", "content": "홍길동 학생 내용",
  "images": [ { "id": 1, "url": "/files/a0fe...e4df.jpg", "display_order": 0, "title": null } ] }
```

### POST /api/admin/lecture-users/{id}/images → 200
```json
[ { "id": 1, "url": "/files/a0fe...e4df.jpg", "display_order": 0, "title": null } ]
```
- multipart `files`(복수). 긴 변 1280px 초과 시 자동 축소, 10MB 초과 JPEG는 품질 저하 재인코딩.
- 5장 초과 → 400 `TOO_MANY_IMAGES`. jpg/jpeg/png 외 → 400 `INVALID_IMAGE_TYPE`.

## 댓글

### GET /api/lectures/{lecture_user_id}/comments (user) / GET /api/admin/lecture-users/{id}/comments (admin) → 200
```json
[ { "id": 1, "lecture_user_id": 1, "author_type": "user", "author_id": 1, "content": "질문 수정", "parent_id": null, "created_at": "..." },
  { "id": 2, "lecture_user_id": 1, "author_type": "admin", "author_id": 1, "content": "답변드립니다", "parent_id": 1, "created_at": "..." } ]
```
- 플랫 배열. `parent_id=null`은 학부모 댓글, `parent_id`가 있으면 관리자 답글(1단계). 프론트에서 부모-답글로 묶음.

### POST /api/lectures/{lecture_user_id}/comments (user) → 201 / 타인 기록 → 404
```json
{ "id": 1, "lecture_user_id": 1, "author_type": "user", "author_id": 1, "content": "질문이 있습니다",
  "parent_id": null, "created_at": "2026-06-01T05:25:39.286805Z" }
```

### GET /api/admin/lectures/{id}/students (admin) → 200
```json
[ { "id": 1, "user_id": 1, "student_name": "홍길동", "title": "홍길동 특강 피드백",
    "content": "홍길동 학생 내용", "images": [ { "id": 1, "url": "/files/...jpg", "display_order": 0, "title": null } ] } ]
```
- PUT/DELETE /api/comments/{id} : 답글 존재 시 → 400 `REPLY_EXISTS`.
- POST /api/comments/{id}/reply (admin) : 답글의 답글 → 400 `NOT_TOP_LEVEL`.
- GET /api/admin/comments/unanswered (admin) : 미답변(관리자 답글 없는 user 댓글) Page.

## 공지

### GET /api/notices (user/admin) → 200 / POST·PUT·DELETE /api/admin/notices (admin)
```json
{ "id": 1, "notice_at": "2026-05-01T09:00:00Z", "serial_no": 1, "admin_id": 1,
  "title": "5월 휴원 안내", "content": "5/5 어린이날 휴원", "images": [] }
```

## MCP (X-API-Key, 읽기 전용)

### GET /api/mcp/lectures → 200 / 키 없음 → 401
```json
{ "items": [ { "id": 1, "lecture_at": "2026-05-20T10:00:00+00:00", "round_no": 1, "subject": "5월 모의고사 해설" } ],
  "total": 1, "page": 1, "size": 10 }
```
### GET /api/mcp/lectures/{id} → 200 (전체 학생 포함)
```json
{ "id": 1, "lecture_at": "...", "round_no": 1, "subject": "...",
  "students": [ { "lecture_user_id": 1, "user_id": 1, "title": "...", "content": "..." } ] }
```
