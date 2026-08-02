# 환경변수 (env_variables.md)

> 값은 `.env`(로컬) 또는 시크릿 매니저(운영)로 주입. `backend/.env.example` 참조.
> **이 문서에는 변수 이름과 형식만 적고 실제 값은 적지 않는다.**

## 필수 — 기본값 없음

아래 세 값은 `config.py` 에 기본값이 없다. 누락되면 기동 시점에 `ValidationError` 로
즉시 중단된다(alembic 단계에서 죽으므로 uvicorn 이 뜨지 않는다).

기본값을 두지 않는 이유: 기본값이 있으면 `.env` 주입에 실패했을 때 조용히 그 값으로
폴백해서, 암호화가 무력화된 줄 모른 채 서비스가 계속 돌아간다.

| 변수 | 형식 | 설명 |
|---|---|---|
| JWT_SECRET | hex 문자열 | JWT 서명 키 |
| NAME_AES_KEY | **32바이트 hex(64자)** | 이름·학번 AES-256-GCM 키 |
| NAME_HMAC_KEY | hex 문자열 | 이름 조회·유니크용 HMAC 키 |

> ⚠️ `NAME_AES_KEY` 는 `app_user.name_enc` 와 `app_user.student_number_enc`
> **두 컬럼에 모두** 쓰인다. 교체하려면 두 컬럼을 함께 재암호화해야 하며,
> 학번을 빠뜨리면 비밀번호 초기화와 사용자 목록이 전부 깨진다.

## 선택 — 기본값 있음

| 변수 | 기본값 | 설명 |
|---|---|---|
| DATABASE_URL | localhost 개발용 URL | DB 연결. docker compose 는 루트 `.env` 값으로 조립해 주입.<br>비밀번호에 `@ : / # ?` 가 있으면 퍼센트 인코딩 필요 |
| JWT_USER_MINUTES | 20 | 학부모 토큰 만료(분) |
| JWT_ADMIN_MINUTES | 240 | 관리자 토큰 만료(분) |
| STORAGE_BACKEND | local | `local` \| `s3` |
| STORAGE_DIR | ./var/uploads | 로컬 업로드 디렉토리 (`local` 일 때) |
| PUBLIC_BASE_URL | /files | 이미지 정적 서빙 경로 prefix |
| S3_BUCKET | (빈 값) | `s3` 일 때 필수 |
| S3_REGION | ap-northeast-2 | |
| S3_PREFIX | uploads/ | 객체 키 prefix |
| S3_PRESIGN_EXPIRES | 3600 | presigned URL 만료(초) |
| AWS_ACCESS_KEY_ID | (빈 값) | `s3` 일 때 필요. IAM 역할 사용 시 생략 |
| AWS_SECRET_ACCESS_KEY | (빈 값) | 동상 |
| MAX_IMAGE_BYTES | 10485760 | 이미지 최대 바이트(초과 시 재압축) |
| IMAGE_MAX_LONG_EDGE | 1280 | 긴 변 최대 px (720p급) |
| MAX_IMAGES_PER_POST | 5 | 게시글당 이미지 수 |
| CORS_ORIGINS | http://localhost:5173 | 허용 오리진(쉼표 구분) |
| COMMENTS_ENABLED | false | 댓글(학부모 댓글/관리자 답글/미답변 인박스) 기능 플래그 |

## 키 생성

```bash
openssl rand -hex 32     # JWT_SECRET / NAME_AES_KEY / NAME_HMAC_KEY 각각 따로 생성
```

## MCP API 키 발급(현재 수동)

```python
from app.security import hash_api_key
print(hash_api_key("발급할-평문-키"))  # 결과를 admin_user.api_key_hash 에 저장
```
