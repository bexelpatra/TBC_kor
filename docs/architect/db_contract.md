# DB 계약 (db_contract.md)

> 작성: Architect | 다음 에이전트: DB
> DB 에이전트는 이 계약을 프로덕션 스키마(schema.md, migrations)로 구체화한다.
> 계약과 다르게 결정할 경우 이유를 schema.md에 명시할 것.

## 공통 메타 (모든 테이블)
- `id` BIGINT PK (auto increment / identity)
- `created_at` (가입/작성 일자), `updated_at` (수정 일자), `deleted_at` NULL (soft delete)
- 조회는 기본적으로 `deleted_at IS NULL` 필터.

표기: **굵게** = 필수(NOT NULL), 그 외 nullable. PK/FK/UNIQUE/INDEX 명시.

---

## user (학부모-자녀 단위 계정)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **phone_tail** | CHAR(4) | NOT NULL, 숫자 4자리 | 학부모 휴대전화 뒷번호 |
| **name_enc** | BYTEA/TEXT | NOT NULL | 자녀 이름 AES 암호문(표시용) |
| **name_hash** | CHAR(64) | NOT NULL | 자녀 이름 HMAC-SHA256(조회·유니크용) |
| **student_number** | CHAR(4) | NOT NULL | 번호 4자리 (제약 없음, 숫자 4자리) |
| **password_hash** | TEXT | NOT NULL | 6자리 숫자 비밀번호 bcrypt 해시 (초기값 `00`+번호 4자리) |
| must_change_pw | BOOL | 기본 true | 최초 로그인 시 변경 유도 |

- UNIQUE(`phone_tail`, `name_hash`) — 동명+동일 뒷번호 충돌 방지, 로그인 조회 키.
- INDEX(`phone_tail`, `name_hash`).

## admin_user (강사/보조자/관리자)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **login_id** | VARCHAR(50) | NOT NULL, UNIQUE, 영문·숫자 | 로그인 ID (메타 `id`와 구분) |
| **password_hash** | TEXT | NOT NULL | 영문·숫자 8자+ bcrypt 해시 |
| **name** | VARCHAR(50) | NOT NULL | 이름(평문 — id/pw/이름은 개인정보 아님) |
| **role** | VARCHAR(10) | NOT NULL | 강사 / 보조자 / 관리자 |
| **level** | SMALLINT | NOT NULL, 1–10 | 권한 레벨(현재 미사용) |
| nickname | VARCHAR(50) | | 닉네임 |
| api_key_hash | TEXT | | MCP용 API 키 해시(읽기 전용) |

## lecture (강의 마스터)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **lecture_at** | TIMESTAMPTZ | NOT NULL | 일시 |
| **round_no** | INT | NOT NULL | 회차 (자동 채번: 직전 최대값+1) |
| **admin_id** | BIGINT | NOT NULL, FK→admin_user.id | 담당 강사 |
| subject | VARCHAR(100) | | 주제(관리자용 라벨) |

- INDEX(`lecture_at`), INDEX(`round_no`).

## lecture_user (학생별 수강 기록 = 게시글, 격리 단위)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **lecture_id** | BIGINT | NOT NULL, FK→lecture.id | 소속 강의 |
| **user_id** | BIGINT | NOT NULL, FK→user.id | 대상 학생 |
| **title** | VARCHAR(200) | NOT NULL | 제목(검색 대상) |
| content | TEXT | | 내용 |

- UNIQUE(`lecture_id`, `user_id`) — 한 강의당 학생 1행.
- INDEX(`user_id`) — 학부모 조회 스코핑. INDEX(`title`) 또는 검색용 인덱스.
- **격리 규칙**: user 대상 모든 조회는 `user_id = 본인` 강제.

## attachment (첨부 이미지, 폴리모픽)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **target_type** | VARCHAR(20) | NOT NULL | 'lecture_user' / 'notice' |
| **target_id** | BIGINT | NOT NULL | 대상 행 id |
| **file_path** | TEXT | NOT NULL | 저장 키/상대경로(S3 이관 대비) |
| **display_order** | SMALLINT | NOT NULL 기본 0 | 정렬 순서 |
| title | VARCHAR(100) | | 제목 |
| note | VARCHAR(255) | | 비고 |

- INDEX(`target_type`, `target_id`).
- 제약(앱 레벨): lecture_user당 최대 5장, jpg/jpeg/png, 10MB 초과 시 720p 재압축 후 저장.

## comment (특강 댓글/답글, 1단계)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **lecture_user_id** | BIGINT | NOT NULL, FK→lecture_user.id | 소속 기록 |
| **author_type** | VARCHAR(10) | NOT NULL | 'user' / 'admin' |
| **author_id** | BIGINT | NOT NULL | 작성자 id |
| **content** | TEXT | NOT NULL | 내용 |
| parent_id | BIGINT | FK→comment.id | 답글이면 부모 댓글(1단계만) |

- INDEX(`lecture_user_id`), INDEX(`parent_id`).
- **미답변** = author_type='user' AND parent_id IS NULL AND (자식 admin 댓글 없음).
- **격리**: user는 자기 `lecture_user`의 자기 댓글 + 그에 달린 admin 답글만 조회. user 수정/삭제는 답글(자식) 생기기 전까지만.

## notice (공지)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| **notice_at** | TIMESTAMPTZ | NOT NULL | 일시 |
| **serial_no** | INT | NOT NULL | 일련번호 (자동 채번: 직전 최대값+1) |
| **admin_id** | BIGINT | NOT NULL, FK→admin_user.id | 작성자 |
| **title** | VARCHAR(200) | NOT NULL | 제목 |
| content | TEXT | | 내용 |

- 이미지는 attachment(target_type='notice').

---

## 주요 접근 패턴
1. user 로그인: `SELECT … FROM user WHERE phone_tail=? AND name_hash=? AND deleted_at IS NULL` → pw 검증.
2. admin 로그인: `WHERE login_id=?` → pw 검증.
3. user 특강 목록: `lecture_user WHERE user_id=본인` + (날짜범위·제목 검색) + 페이징(LIMIT/OFFSET) + 최신순.
4. user 특강 상세: 위 조건의 단건 + attachment + 본인 댓글/admin 답글.
5. admin 미답변 인박스: user 댓글 중 자식 admin 답글 없는 것.
6. MCP 조회: lecture/lecture_user/notice 읽기 전용 검색.

## 시드 데이터
- 최초 관리자 1개: `login_id=master`, 비밀번호는 환경변수 `MASTER_ADMIN_PASSWORD`로 주입(bcrypt 해시 저장, 평문 기록 금지), `name`·`role`·`level`은 임의(예: name='마스터', role='관리자', level=10).
- 시드 스크립트로 1회 생성. 이후 관리자는 관리자가 추가.
