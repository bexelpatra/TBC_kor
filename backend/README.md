# BRAIN_CORE_KOR Backend (FastAPI)

## 로컬 실행

```bash
conda activate web
cd backend
pip install -r requirements.txt

# 1) PostgreSQL 준비 (예: 도커)
docker run -d --name brain_core_kor-pg -e POSTGRES_USER=brain_core_kor -e POSTGRES_PASSWORD=brain_core_kor \
  -e POSTGRES_DB=brain_core_kor -p 5432:5432 postgres:16

# 2) 환경설정
cp .env.example .env        # DATABASE_URL 등 확인/수정

# 3) 마이그레이션 + 시드
alembic upgrade head
MASTER_ADMIN_PASSWORD='원하는 비밀번호' python -m app.seed   # 최초 관리자 master 계정 생성

# 4) 서버
uvicorn app.main:app --reload --port 8000
```

- API 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

## 구조
```
app/
├── main.py          # 앱 진입점, 라우터 등록, CORS, 에러 핸들러, 정적 서빙
├── config.py        # 환경설정
├── database.py      # 엔진/세션/Base
├── models.py        # SQLAlchemy 모델
├── schemas.py       # Pydantic
├── security.py      # bcrypt, AES-GCM 이름암호화, HMAC, JWT, API키
├── deps.py          # 인증/권한 의존성(require_level 골격)
├── storage.py       # 파일 저장 추상화 + 이미지 720p 리사이즈
├── numbering.py     # 회차/일련번호 자동 채번
├── excel.py         # 사용자 일괄등록 양식/파싱
├── pagination.py    # 페이징(10/20/30)
└── routers/         # auth, admin_users, admin_lectures, lectures, comments, notices, mcp
alembic/             # 마이그레이션 (0001_init = docs/db/migrations/V001 동일)
```
