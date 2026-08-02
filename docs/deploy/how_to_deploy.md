# 배포 방법 (현재 운영 방식 — docker-compose)

> 이 문서는 **지금 이 서버에서 실제로 쓰고 있는** docker-compose 기반 배포 방법을 정리한 실전 가이드입니다.
> 향후 AWS(EC2/RDS/S3 등) 이관 계획은 `deployment_plan.md` 참고.

---

## 1. 전체 구조

```
docker-compose.yml
├── db        : PostgreSQL 16 (포트 55433 → 5432)
├── api       : FastAPI/uvicorn (포트 8088 → 8000)  ← backend/
└── frontend  : Vue 빌드 결과를 nginx로 서빙 (포트 5173 → 80)  ← frontend/
```

- **backend**: 코드가 `./backend`를 컨테이너의 `/app`에 그대로 마운트 + `--reload` 옵션이라, 컨테이너만 살아있으면 **코드 수정 즉시 반영**(다만 `requirements.txt`나 Dockerfile 자체를 바꾼 경우엔 재빌드 필요).
- **frontend**: Vite로 빌드한 정적 파일을 nginx 이미지에 굽는 방식이라, **코드를 바꾼 뒤에는 반드시 이미지를 다시 빌드**해야 반영됩니다.
- 컨테이너 시작 시 `api`는 `alembic upgrade head`를 자동 실행 → DB 마이그레이션이 항상 최신 상태로 맞춰짐.

---

## 2. 사전 준비 — 환경변수

| 파일 | 용도 |
|---|---|
| `backend/.env` | JWT 시크릿, 암호화 키, 스토리지/이미지 정책, CORS, 마스터 관리자 비밀번호 등 |
| `frontend/.env` | `VITE_API_BASE` — 프론트가 호출할 백엔드 주소 (빌드 시점에 박힘) |

```bash
# 최초 1회만 (이미 있으면 생략)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

> `frontend/.env`의 `VITE_API_BASE`는 **빌드할 때 정적 파일에 박혀버리므로**, 값을 바꾸면 반드시 `frontend` 이미지를 재빌드해야 합니다.

---

## 3. 백엔드 배포 (`backend/`)

### 3-1. 처음 띄우기 / 전체 재빌드

```bash
docker-compose build api
docker-compose up -d api
```

- `api` 컨테이너 커맨드: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- 즉, **컨테이너가 뜨는 시점에 DB 마이그레이션이 자동 적용**됩니다.

### 3-2. 코드만 수정한 경우 (가장 흔한 경우)

`./backend`가 볼륨 마운트 + `--reload`라서, **별도 빌드 없이 코드 수정만으로 자동 반영**됩니다.
로그로 reload 확인:

```bash
docker logs -f tbc_kor_api_1
```

### 3-3. `requirements.txt` / `Dockerfile` / `alembic` 새 마이그레이션을 추가한 경우

이미지 자체를 다시 빌드해야 합니다 (의존성 설치, 새 마이그레이션 적용 포함):

```bash
docker-compose build api
docker rm -f tbc_kor_api_1     # docker-compose 1.29.x 버그 회피용 (3-5 참고)
docker-compose up -d api
```

### 3-4. 마이그레이션만 수동으로 적용하고 싶을 때

보통은 컨테이너 재시작 시 자동 적용되지만, 컨테이너를 안 내리고 바로 적용하고 싶으면:

```bash
docker exec tbc_kor_api_1 alembic upgrade head
```

### 3-5. (트러블슈팅) `docker-compose up -d` 시 `ContainerConfig` KeyError

`docker-compose` 1.29.2 + 최신 docker 이미지 포맷 조합에서 `Recreating` 단계가 깨지는 알려진 버그입니다.
재현되면 아래처럼 기존 컨테이너를 지우고 다시 올리면 됩니다 (DB 볼륨은 그대로라 데이터 손실 없음):

```bash
docker rm -f tbc_kor_api_1
docker-compose up -d api
```

### 3-6. 로그 / 상태 확인

```bash
docker ps --format "{{.Names}}\t{{.Status}}"
docker logs --tail 50 tbc_kor_api_1
docker logs -f tbc_kor_api_1        # 실시간
```

---

## 4. 프론트엔드 배포 (`frontend/`)

Vue(Vite) → `npm run build` → 결과물(`dist/`)을 nginx 이미지에 복사하는 **멀티스테이지 빌드**입니다.
**코드/환경변수를 바꾸면 반드시 이미지를 재빌드**해야 화면에 반영됩니다.

### 4-1. 코드 수정 후 배포 (가장 흔한 경우)

```bash
docker-compose build frontend
docker rm -f tbc_kor_frontend_1     # 3-5와 동일한 이유
docker-compose up -d frontend
```

### 4-2. `VITE_API_BASE`(백엔드 주소)를 바꿔야 할 때

`frontend/.env` 수정 후, build arg로 다시 빌드:

```bash
# docker-compose.yml의 args.VITE_API_BASE 가 ${VITE_API_BASE:-...} 를 참조
export VITE_API_BASE=https://api.example.com
docker-compose build frontend
docker rm -f tbc_kor_frontend_1
docker-compose up -d frontend
```

### 4-3. 빌드 결과만 빠르게 확인하고 싶을 때 (컨테이너 없이)

```bash
cd frontend
npm ci
npm run build       # dist/ 생성, vite.config의 VITE_API_BASE는 frontend/.env 사용
npm run preview     # 로컬에서 미리보기 (배포용은 아님)
```

---

## 5. 한 번에 전체 재배포

```bash
docker-compose build           # api + frontend 모두 재빌드 (db는 image라 스킵됨)
docker rm -f tbc_kor_api_1 tbc_kor_frontend_1
docker-compose up -d
```

`db`는 처음 1회 `docker-compose up -d`로 띄운 뒤엔 보통 그대로 유지(데이터는 `pgdata` 볼륨에 영속).

---

## 6. 자주 쓰는 명령어 모음

| 목적 | 명령어 |
|---|---|
| 전체 상태 확인 | `docker ps --format "{{.Names}}\t{{.Status}}"` |
| 특정 컨테이너 로그 | `docker logs --tail 100 -f tbc_kor_api_1` |
| 백엔드만 재빌드+재기동 | `docker-compose build api && docker rm -f tbc_kor_api_1 && docker-compose up -d api` |
| 프론트만 재빌드+재기동 | `docker-compose build frontend && docker rm -f tbc_kor_frontend_1 && docker-compose up -d frontend` |
| 마이그레이션 수동 적용 | `docker exec tbc_kor_api_1 alembic upgrade head` |
| 컨테이너 안에서 셸 | `docker exec -it tbc_kor_api_1 bash` |
| DB 콘솔 접속 | `docker exec -it tbc_kor_db_1 psql -U admin -d brain_core_kor` |
| 전체 중지 | `docker-compose down` (볼륨은 유지됨, `-v` 붙이면 DB 데이터까지 삭제되므로 주의) |

---

## 7. 배포 체크리스트 (요약)

- **백엔드 코드만 수정** → 아무것도 안 해도 `--reload`로 자동 반영 (로그로 확인)
- **백엔드 의존성/마이그레이션/Dockerfile 수정** → `build api` → `rm -f` → `up -d api`
- **프론트 코드/환경변수 수정** → `build frontend` → `rm -f` → `up -d frontend`
- 항상 마지막엔 `docker ps`와 `docker logs`로 정상 기동(에러 없이 `Application startup complete.`) 확인

---

## 8. 운영(클라우드) 이관 시

VM 분리, S3, Cloudflare Pages, CI/CD(Jenkins) 등 향후 계획은 `deployment_plan.md`에 정리되어 있습니다.
지금은 **단일 서버 + docker-compose** 구조이며, 위 절차만으로 배포/업데이트가 충분합니다.
