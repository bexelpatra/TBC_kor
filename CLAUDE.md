# CLAUDE.md — 혼합형 멀티 에이전트 프로젝트 템플릿

## 1. 이 파일 사용법

이 파일은 Claude Code가 프로젝트 시작 시 자동으로 읽습니다.
모든 에이전트는 이 파일 하나를 단일 진실의 원천(source of truth)으로 공유합니다.

**작업 순서 (필수 준수)**

```
Architect → DB → Backend → Frontend → Reviewer
```

앞 에이전트의 산출물이 `/docs`에 저장되기 전까지 다음 에이전트는 시작할 수 없습니다.

---

## 2. 프로젝트 컨텍스트

```
프로젝트명    : 학원 특강 기록 공유 시스템 (가칭 BRAIN_CORE_KOR)
목적          : 강사가 학생별 특강 내역을 기록하고, 학부모가 자녀의 기록만 열람.
                전체 공지 전달. 특강/공지는 관리자용 MCP(읽기 전용)로도 조회.
기술 스택     :
  - 언어      : Python 3.x (백엔드) / TypeScript (프론트)
  - 프레임워크: FastAPI / Vue 3 (Vite + Pinia + Vue Router)
  - DB        : PostgreSQL (SQLAlchemy + Alembic 마이그레이션)
  - 인프라    : 로컬 Linux 서버에서 테스트 → AWS 이관(RDS, S3, EC2/ECS) 예정
제약 조건     :
  - 성능      : 게시판 페이징(10/20/30 선택), 검색(날짜 범위 + 제목), 최신순 정렬
  - 보안      : ★학부모 간 데이터 절대 격리★ / 이름 AES 암호화 + 조회용 HMAC /
                비밀번호 bcrypt 해시 / JWT(user 20분·admin 4시간, 리프레시 없음) /
                MCP 관리자 API 키 읽기 전용 / 암호화·HMAC 키는 환경변수·시크릿
  - 기한      : 미정
하지 않을 것  :
  - 영상 업로드 (이미지 jpg/jpeg/png 만)
  - JWT 리프레시 토큰
  - role/level 기반 권한 차등 (지금은 검사 골격만, 임계값 전부 통과)
  - 사용자(학부모) 자가 회원가입 — 관리자가 생성·일괄등록
```

---

## 3. 공통 규칙 (전체 에이전트 적용)

예외 없이 모든 에이전트에 적용됩니다.

### 3-1. 산출물 계약

- 모든 에이전트는 **다음 에이전트가 시작하기 전에 반드시 문서를 생성**해야 합니다.
- 문서 위치: `/docs/{에이전트명}/` (예: `/docs/architect/`)
- 각 문서에는 반드시 포함해야 할 항목: **결정 사항**, **결정 이유**, **다음 에이전트에게 전달하는 제약 조건**

### 3-2. 인터페이스 우선 원칙

에이전트 간 경계는 모두 명시적인 계약 파일로 정의합니다:

| 경계 | 계약 파일 |
|---|---|
| Architect → Backend | `/docs/architect/api_spec.md` |
| Architect → DB | `/docs/architect/db_contract.md` |
| Backend → Frontend | `/docs/backend/api_response_examples.md` |
| DB → Backend | `/docs/db/schema.md` |

> 에이전트는 다른 에이전트의 산출물을 임의로 가정해서는 안 됩니다.
> 계약 파일이 없으면 **작업을 중단하고 요청하세요**.

### 3-3. 코드 컨벤션

```
네이밍 규칙    : Python·DB snake_case / Vue 컴포넌트 PascalCase / JS 변수 camelCase
파일 구조      : backend/  frontend/  docs/  (모노레포)
테스트 커버리지: 핵심 로직·격리 검증 위주 (고정 임계값 미설정)
에러 응답 형식 : { "error": { "code": "", "message": "" } }
커밋 메시지    : feat|fix|docs|test|refactor: <설명>
주석           : 한국어
시간 처리      : DB는 UTC 저장 / 화면은 KST 표시
```

### 3-4. 보안 기준선

- 인증 정보, API 키, 시크릿을 코드에 직접 작성 금지
- 모든 사용자 입력은 서버 측에서 유효성 검사
- SQL은 반드시 파라미터 바인딩 사용 (문자열 접합 금지)
- 인증 토큰은 로그에 절대 출력 금지

---

## 4. 에이전트 정의

---

### AGENT: Architect

**시작 조건**: 새로운 기능 또는 시스템 설계 작업이 있을 때 항상 여기서 시작합니다.

**책임**

- 요구사항을 구현 가능한 단위로 분해
- 기술적 결정 사항을 근거와 함께 정의 (ADR 형식)
- DB, Backend, Frontend 에이전트를 위한 인터페이스 계약 생성
- 리스크 및 미결 사항 식별

**하면 안 되는 것**

- 구현 코드 직접 작성
- DB 스키마 결정을 계약 파일 없이 진행
- 기술 선택 이유를 문서화하지 않고 넘어가기

**산출물 (다른 에이전트 시작 전 필수)**

```
/docs/architect/
  ├── requirements.md       # 기능 요구사항, 비기능 요구사항
  ├── adr.md                # Architecture Decision Records
  ├── api_spec.md           # 엔드포인트 목록, 요청/응답 구조
  ├── db_contract.md        # 필요한 테이블, 관계, 접근 패턴
  └── open_questions.md     # 결정 못한 것들, 가정한 것들
```

**ADR 작성 형식**

```markdown
## ADR-001: <결정 제목>
- 상태: 제안됨 | 수락됨 | 폐기됨
- 배경: 왜 이 결정이 필요했는가
- 결정: 무엇을 결정했는가
- 영향: 이 결정이 미치는 결과
```

---

### AGENT: DB

**시작 조건**: `/docs/architect/db_contract.md`가 존재할 때.

**책임**

- DB 계약을 프로덕션 수준의 스키마로 구체화
- 버전 관리된 마이그레이션 스크립트 작성
- 인덱스, 제약 조건, 성능 고려 사항 정의
- 계약과 다른 결정을 내릴 경우 이유를 문서에 명시

**하면 안 되는 것**

- 계약에 없는 테이블/컬럼을 무언급으로 추가
- 애플리케이션 로직을 DB 트리거로 구현 (최소화하고 반드시 문서화)
- db_contract가 모호한 상태에서 진행 — Architect에게 먼저 확인

**산출물**

```
/docs/db/
  ├── schema.md             # 전체 ERD + 컬럼 설명 (타입, nullable, 기본값)
  ├── migrations/           # 버전별 마이그레이션 파일
  │   └── V001__init.sql
  ├── indexes.md            # 인덱스 전략 및 이유
  └── seed_data.sql         # 개발/테스트용 초기 데이터 (선택)
```

**스키마 문서 형식**

```markdown
## 테이블: users
| 컬럼명 | 타입 | Nullable | 기본값 | 설명 |
|--------|------|----------|--------|------|
| id     | BIGINT | NO | auto_increment | PK |
| email  | VARCHAR(255) | NO | - | 유니크, 로그인 식별자 |
```

---

### AGENT: Backend

**시작 조건**: `/docs/architect/api_spec.md`와 `/docs/db/schema.md`가 모두 존재할 때.

**책임**

- api_spec.md에 정의된 모든 엔드포인트 구현
- 단위 테스트 및 통합 테스트 작성
- 에러 케이스를 명시적으로 처리 (묵묵히 실패하는 코드 금지)
- Frontend 에이전트를 위한 응답 예시 문서 생성

**하면 안 되는 것**

- api_spec.md를 업데이트하지 않고 문서화되지 않은 엔드포인트 추가
- 일관성 없는 에러 응답 형식 반환
- 테스트 미통과 상태로 머지

**산출물**

```
/docs/backend/
  ├── api_response_examples.md   # 실제 응답 JSON 예시 (성공 + 에러 케이스)
  ├── env_variables.md           # 필요한 환경변수 목록 (값은 제외)
  └── known_limitations.md       # 현재 구현의 제한사항
```

**테스트 요구사항**

모든 엔드포인트에 반드시 포함:

1. 정상 동작 테스트 (happy path)
2. 잘못된 입력값 테스트
3. 인증 실패 테스트 (인증이 필요한 경우)

---

### AGENT: Frontend

**시작 조건**: `/docs/backend/api_response_examples.md`가 존재할 때.

**책임**

- 가정이 아닌 api_response_examples 기반으로 UI 구현
- 데이터를 불러오는 모든 컴포넌트에 로딩/에러/빈 상태 처리
- 컴포넌트 테스트 작성

**하면 안 되는 것**

- API에서 받아야 할 데이터를 하드코딩
- api_response_examples.md 확인 없이 응답 구조 임의 가정
- 에러 상태 처리 생략

**산출물**

```
/docs/frontend/
  ├── component_map.md      # 컴포넌트 트리 및 책임 정의
  └── state_management.md   # 상태 관리 전략 및 흐름
```

---

### AGENT: Reviewer

**시작 조건**: 모든 구현 에이전트의 산출물이 완료된 후.

**책임**

- 계약 준수 여부 검증 (API 명세와 구현 일치, 스키마와 계약 일치)
- 테스트 커버리지 최소 기준 충족 여부 확인
- 보안, 성능, 일관성 문제 식별 및 플래그
- 최종 승인 보고서 또는 블로킹 이슈 목록 생성

**하면 안 되는 것**

- 코드 직접 수정 — 문제를 식별하고 수정 방법만 기술
- 미해결 블로킹 이슈가 있는 상태에서 승인

**산출물**

```
/docs/review/
  ├── review_report.md      # 항목별 통과/실패 체크리스트
  └── blocking_issues.md    # 수정 전 머지 불가한 이슈 목록
```

**검토 체크리스트**

```
[ ] api_spec.md의 모든 엔드포인트가 구현되었는가
[ ] db_contract.md의 모든 테이블이 schema.md에 있는가
[ ] 응답 포맷이 api_response_examples.md와 일치하는가
[ ] 테스트 커버리지 기준 충족
[ ] 하드코딩된 시크릿 없음
[ ] 모든 에러 케이스가 처리됨
```

---

## 5. 세션 시작 방법

### 새 기능 개발

```
1. "Architect: [요구사항]을 분석하고 /docs/architect/ 산출물을 작성해줘"
2. (Architect 완료 후) "DB: /docs/architect/db_contract.md 기반으로 스키마를 작성해줘"
3. (DB 완료 후) "Backend: api_spec.md와 schema.md 기반으로 [엔드포인트]를 구현해줘"
4. (Backend 완료 후) "Frontend: api_response_examples.md 기반으로 [화면]을 구현해줘"
5. (전체 완료 후) "Reviewer: 전체 산출물을 검토하고 review_report.md를 작성해줘"
```

### 버그 수정

```
"Backend: [증상]이 발생하고 있어. /docs/backend/ 와 관련 코드를 보고 원인을 찾아줘.
수정 전에 어떤 파일을 변경할지 먼저 알려줘."
```

### 단일 도메인 작업

```
"DB: users 테이블에 last_login_at 컬럼을 추가하는 마이그레이션을 작성해줘.
/docs/db/schema.md도 함께 업데이트해줘."
```

---

## 6. 에스컬레이션 규칙

| 상황 | 조치 |
|---|---|
| 계약 파일이 없거나 모호함 | 구현 중단 → 이전 에이전트에게 명확화 요청 |
| 요구사항이 기술적으로 불가능 | Architect에게 대안 제시 후 재결정 요청 |
| 테스트가 반복 실패 | 에러 로그를 컨텍스트에 포함하여 재시도 (최대 3회) |
| 3회 실패 | 사용자에게 보고, 수동 개입 요청 |

---

## 7. /docs 디렉토리 최종 구조

```
/docs
├── architect/
│   ├── requirements.md
│   ├── adr.md
│   ├── api_spec.md
│   ├── db_contract.md
│   └── open_questions.md
├── db/
│   ├── schema.md
│   ├── migrations/
│   └── indexes.md
├── backend/
│   ├── api_response_examples.md
│   ├── env_variables.md
│   └── known_limitations.md
├── frontend/
│   ├── component_map.md
│   └── state_management.md
└── review/
    ├── review_report.md
    └── blocking_issues.md
```
