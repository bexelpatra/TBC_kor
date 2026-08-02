# 배포 계획 — 단일 VM + docker-compose (④ 단계)

> 관련 결정: `/docs/architect/adr.md` ADR-012
> 대상 규모: 사용자 200~1000명, ~3만 건/일(평균 0.35 req/s, 피크 5~10 req/s)

---

## 1. 결정 사항

- **VM 1대**(AWS EC2 `t4g.small` 2vCPU/2GB, 또는 AWS Lightsail $10/2GB)에 **docker-compose**로 3개 컨테이너 구동:
  - `api` — FastAPI(uvicorn/gunicorn)
  - `db` — PostgreSQL 16
  - `caddy` — 리버스 프록시 + Let's Encrypt 자동 TLS
- **이미지 저장소**는 **1단계: VM 디스크(로컬)**로 시작. `STORAGE_BACKEND=local`, `backend/var/uploads`를 docker volume으로 영속화. **동작 확인 후 2단계로 S3/R2 전환** 검토(ADR-013).
- **프론트(Vue 정적 빌드)**는 **Cloudflare Pages**(무료, git 연동 자동 배포). VM에 안 올림.
- **DB 백업**은 RDS 대신 `pg_dump` → 오브젝트 스토리지 **일 1회 cron**. (이미지 디렉토리도 1단계부터 함께 백업 — 아래 5-4 참고)
- **시크릿**은 코드/이미지에 넣지 않고 VM의 `.env.prod`(권한 600) 또는 AWS SSM Parameter Store에서 주입.

## 2. 결정 이유

- 트래픽이 작아 매니지드 서비스(RDS/App Runner)를 따로 상시 가동하면 idle 비용만 누적됨(월 $35~90). 한 대에 합치면 **월 ~$10~12 고정**.
- Lightsail 인스턴스에 SSD 스토리지가 ~60GB 포함되어 있고, 이미지 정책(jpg/png, 10MB 제한, 5장/포스트, 사용자 200~1000명) 기준 누적량이 수 GB 수준 → **1단계에서 S3 불필요**. 코드도 `LocalStorage`가 이미 구현돼 있어 추가 작업 없음.
- 코드는 이미 클라우드 친화적: `storage.py`가 `save/delete/url` 인터페이스로 추상화돼 있어, 필요해지면 `S3Storage`만 추가하면 됨(ADR-007, ADR-013). 설정은 전부 env 주입(`config.py`).
- 확장 경로 유지: 부하/용량이 커지면 **이미지만 S3로 분리**(`STORAGE_BACKEND=s3`)하거나, **DB만 RDS로 분리**(`DATABASE_URL` 교체)하거나 VM을 키우면 됨. 코드 변경 거의 없음.

## 3. 다음 작업자(Backend/DevOps)에게 전달하는 제약

- 이미지 정적 서빙: `main.py`는 `storage_backend == "local"`일 때 `/files`를 `StaticFiles`로 마운트함 — **1단계는 이 경로 그대로 사용**. `backend/var/uploads`는 docker volume으로 컨테이너 재생성 시에도 유지되도록 마운트.
- `PUBLIC_BASE_URL`은 1단계에서도 **운영 도메인 절대 URL + `/files`**(예: `https://api.example.com/files`)로 설정 — 프론트와 API 도메인이 다르므로 상대경로(`/files`)는 안 됨.
- **2단계(S3 전환) 시**: 이 마운트는 비활성되고, 이미지 URL은 버킷의 공개 URL(또는 presigned)을 반환해야 함 → `S3Storage.url()`이 절대 URL을 돌려주도록 구현. 기존 로컬 이미지는 마이그레이션(버킷 업로드 + DB의 URL 경로 갱신) 필요.
- `name_aes_key` 분실 = 암호화된 학생 이름 **영구 복구 불가**. 운영 키 생성 후 별도 안전 보관 필수(ADR-003).

---

## 4. 아키텍처

```
[브라우저]
   │  HTTPS
   ├──────────────► Cloudflare Pages  (프론트 정적: Vue dist)
   │                      │ 빌드 시 VITE_API_BASE = https://api.example.com
   │  XHR (HTTPS)         ▼
   └──────────────► api.example.com  ─┐
                                       │  VM 1대 (t4g.small / Lightsail 2GB)
   ┌───────────────────────────────────────────────────────┐
   │  docker-compose                                         │
   │    caddy(:443/:80)  ──► api(:8077, uvicorn) ──► db(:5432, postgres)  │
   │       │  자동 TLS                  │            │                     │
   │       └─ /health, /api/*           └─ /files (LocalStorage)         │
   │                                        var/uploads (volume)          │
   └───────────────────────────────────────────────────────┘
                                        ▲
                          pg_dump + uploads tar cron (일 1회) ──► S3 / R2 (백업)
```

- 1단계: 이미지는 `https://api.example.com/files/<key>`로 API가 직접 서빙(StaticFiles).
- API와 정적 프론트의 도메인이 다르므로 **CORS에 프론트 도메인 등록 필수**(`CORS_ORIGINS`).
- 2단계(S3 전환) 시: 이미지 응답 URL이 버킷 공개 URL(예: `https://cdn.example.com/<key>`)로 바뀌고, 브라우저가 버킷에서 직접 로드.

---

## 5. 추가할 파일 (코드 작업, 승인 후 진행)

```
backend/
  Dockerfile                # python:3.12-slim, requirements 설치, gunicorn+uvicorn worker
deploy/
  docker-compose.yml        # api / db / caddy
  Caddyfile                 # api.example.com → api:8077 리버스 프록시 + 자동 TLS
  .env.prod.example         # 운영 env 템플릿(값 제외)
  backup.sh                 # pg_dump + uploads → S3 업로드 (cron 등록용)
  deploy.sh                 # git pull → build → compose up -d → alembic upgrade
Jenkinsfile                 # CI/CD 파이프라인 (6장 참조)
```

> 1단계(로컬 스토리지)에서는 `app/storage_s3.py`/`storage.py` 분기 작업 **불필요** — 기존 `LocalStorage` 그대로 사용. 2단계 전환 시 ADR-013 참고해 추가.

### 5-1. `docker-compose.yml` 골격
```yaml
services:
  db:
    image: postgres:16
    environment: [POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]
    volumes: ["pgdata:/var/lib/postgresql/data"]   # VM 디스크에 영속
    restart: unless-stopped
  api:
    build: ../backend
    env_file: .env.prod
    depends_on: [db]
    restart: unless-stopped
    volumes: ["uploads:/app/var/uploads"]   # 이미지 영속 (STORAGE_BACKEND=local)
    # 시작 시 alembic upgrade head 후 gunicorn 기동(entrypoint)
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes: ["./Caddyfile:/etc/caddy/Caddyfile", "caddy_data:/data"]
    depends_on: [api]
    restart: unless-stopped
volumes: { pgdata: {}, caddy_data: {}, uploads: {} }
```

### 5-2. `Caddyfile` (TLS 자동)
```
api.example.com {
    reverse_proxy api:8077
}
```

### 5-3. `backup.sh` 골격 (1단계: DB + 이미지 함께 백업)
```bash
# pg_dump → 압축 → S3 업로드
pg_dump $DATABASE_URL | gzip > /tmp/db_$(date +%F).sql.gz
# uploads 볼륨 → tar → S3 업로드 (이미지도 백업 대상에 포함)
tar -czf /tmp/uploads_$(date +%F).tar.gz -C /app/var uploads
# 둘 다 aws s3 cp (또는 r2) 로 백업용 버킷에 업로드
```

---

## 6. Git + Jenkins — 가능함 (권장 구성 포함)

**결론: 완전히 가능하다.** docker-compose 배포는 Jenkins/GitHub Actions/GitLab CI 어느 것과도 잘 맞는다. 다만 **Jenkins를 운영 VM(2GB)에 같이 올리면 안 된다** — Jenkins는 JVM + 빌드에 1~2GB를 잡아먹어 앱과 DB를 굶긴다.

### 6-1. 권장 배치
- **Git 호스트**: GitHub / GitLab / 자체 Gitea 중 택1. (현재 프로젝트는 아직 `git init` 안 됨 → 1단계에서 저장소화 필요.)
- **Jenkins 위치**: 운영 VM이 **아닌** 별도 머신. 후보 ① 사내 로컬 Linux 서버(테스트용으로 이미 있음) ② 별도 빌드 인스턴스. Jenkins는 **빌드/테스트만** 하고, 결과물을 운영 VM에 전달.
- **운영 VM 접근**: Jenkins → 운영 VM에 **SSH 배포 키**(배포 전용·최소권한)로 접속.

### 6-2. 파이프라인 흐름 (`Jenkinsfile`)
```
1. Checkout        : git에서 소스 받기 (push/PR 머지 시 webhook 트리거)
2. Test            : 백엔드 pytest (격리/인증 케이스 포함)
3. Build           : docker build → 이미지에 커밋 SHA 태그
4. Push            : 레지스트리에 push (AWS ECR / GHCR / Docker Hub)
5. Deploy          : 운영 VM에 ssh →
                       docker compose pull && docker compose up -d
                       (api 컨테이너 기동 시 alembic upgrade head 자동 실행)
6. Smoke test      : curl https://api.example.com/health 200 확인
```

`Jenkinsfile`(선언형) 골격:
```groovy
pipeline {
  agent any
  stages {
    stage('Test')   { steps { sh 'cd backend && pip install -r requirements.txt && pytest' } }
    stage('Build')  { steps { sh 'docker build -t $REG/brain_core_kor-api:$GIT_COMMIT backend' } }
    stage('Push')   { steps { sh 'docker push $REG/brain_core_kor-api:$GIT_COMMIT' } }
    stage('Deploy') { steps {
      sshagent(['brain_core_kor-prod-deploy']) {
        sh '''ssh deploy@$PROD_HOST "cd /opt/brain_core_kor/deploy && \
              IMAGE_TAG=$GIT_COMMIT docker compose pull api && \
              IMAGE_TAG=$GIT_COMMIT docker compose up -d"'''
      }
    } }
  }
}
```

### 6-3. 프론트 배포
- **Cloudflare Pages**가 git 연동으로 push 시 자동 빌드(`npm run build`)·배포 → 별도 Jenkins 단계 불필요.
- Jenkins로 통일하고 싶으면: `npm run build` → `dist`를 S3/Pages에 업로드하는 stage 추가.

### 6-4. 더 가벼운 대안(참고)
- Jenkins 인프라가 부담이면 **GitHub Actions**가 이 규모엔 더 간단(러너 무료, 위 흐름 동일). 단, 사내 표준이 Jenkins면 위 6-2 그대로 가면 됨.

---

## 7. 운영 env 변수 (값 제외, `deploy/.env.prod`)

| 변수 | 비고 |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://brain_core_kor:<pw>@db:5432/brain_core_kor` (compose 내부 호스트명 `db`) |
| `JWT_SECRET` | **신규 생성** `openssl rand -hex 32` |
| `NAME_AES_KEY` | **신규 생성** `openssl rand -hex 32` (32바이트). ⚠️ 분실 시 복호화 불가 — 별도 보관 |
| `NAME_HMAC_KEY` | **신규 생성** `openssl rand -hex 32` |
| `STORAGE_BACKEND` | `local` (1단계) |
| `PUBLIC_BASE_URL` | `https://api.example.com/files` (API 도메인 + `/files`, 절대경로) |
| `CORS_ORIGINS` | 프론트 운영 도메인 (예 `https://brain_core_kor.example.com`) |
| `S3_BUCKET` / `S3_ENDPOINT` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_REGION` | **백업용 버킷** (1단계부터 `backup.sh`에서 사용. R2면 `S3_ENDPOINT`에 R2 엔드포인트) |
| `JWT_USER_MINUTES` / `JWT_ADMIN_MINUTES` | 20 / 240 (기존 정책 유지) |

프론트(`frontend/.env.production`): `VITE_API_BASE=https://api.example.com`

---

## 8. 배포 절차 (수동 1회 → 이후 CI)

- [x] 0. 프로젝트 `git init` + 원격 저장소 연결, `.gitignore`에 `.env*`, `var/`, `dist/` 추가
- [ ] 1. VM 프로비저닝(Lightsail 2GB), Docker + docker-compose 설치
- [ ] 2. 도메인 2개 DNS A레코드 → VM IP (`api.example.com`), Cloudflare Pages(`brain_core_kor.example.com`)
- [ ] 3. S3/R2 **백업용 버킷** 생성, 접근 키 발급 (이미지용 버킷은 2단계에서)
- [ ] 4. 운영 시크릿 생성(`openssl rand -hex 32` ×3), `.env.prod` 작성(권한 600) — `STORAGE_BACKEND=local`
- [ ] 5. `Dockerfile` / `docker-compose.yml`(uploads volume 포함) / `Caddyfile` 작성
- [ ] 6. VM에서 `docker compose up -d` → `alembic upgrade head` → 시드 관리자 생성
- [ ] 7. 프론트 `.env.production` 설정 → Cloudflare Pages 빌드/배포
- [ ] 8. 스모크 테스트: 로그인, 강의/공지 작성, 이미지 업로드/조회, 학부모 격리 확인
- [ ] 9. `backup.sh` cron 등록(일 1회 `pg_dump` + uploads tar → S3 백업 버킷), 복원 1회 리허설
- [ ] 10. Jenkins(또는 Actions) 파이프라인 연결 → push 시 자동 배포 확인
- [ ] 11. (운영 안정화 후, 필요 시) **2단계: S3 전환** — `S3Storage` 구현, 기존 이미지 마이그레이션 (ADR-013)

---

## 9. 비용 요약 (월, 대략)

| 항목 | 비용 |
|---|---|
| VM (Lightsail 2GB, ~60GB SSD 포함) | $10 |
| S3/R2 백업용 (DB dump + 이미지, 수 GB) | ~$0.5 |
| Cloudflare Pages (프론트) | $0 |
| 도메인 | ~$1 (연 $12) |
| **합계** | **~$11~12 고정** |

> 2단계(이미지 S3 전환) 시 +이미지 버킷/전송 비용 추가(소규모면 ~$1 수준).

> 1년 약정(Savings Plan)·프리티어 적용 시 더 절감. DB 분리(RDS) 필요해지면 +$15 수준.

---

## 10. 리스크 / 미결 사항

- **단일 VM = 단일 장애점**: VM 다운 시 전체 중단(이미지 포함, 1단계는 로컬 디스크). 이 규모 허용이나, 복구는 "스냅샷 + compose 재기동 + 백업 복원"으로 대비. HA 필요해지면 DB를 RDS로, 이미지를 S3로 분리.
- **DB/이미지 백업 책임이 우리에게**: cron 누락/실패 감지 필요(백업 성공 알림). 복원 리허설을 최소 1회 수행.
- **VM 디스크 용량 모니터링**: ~60GB 중 이미지+DB+로그 사용량 추적. 용량 압박 시 2단계(S3 전환) 트리거로 사용.
- **이미지 접근 제어**: 1단계는 API(`/files`)를 통해서만 접근(인증 미들웨어 적용 범위 확인 필요). 2단계 S3 전환 시 공개 버킷 URL은 키만 알면 접근 가능 → 학생 기록 이미지 격리 필요하면 **presigned URL** 검토.
- **컨테이너 메모리**: 2GB에 Postgres+API 공존 → 동시 사용자 급증 시 모니터링 후 4GB로 상향 판단.
- **Jenkins 위치 미정**: 사내 로컬 서버 재사용 vs 별도 인스턴스 — 6-1 기준으로 사용자 확인 필요.
