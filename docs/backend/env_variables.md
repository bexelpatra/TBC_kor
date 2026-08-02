# 환경변수 (env_variables.md)

> 값은 `.env`(로컬) 또는 시크릿 매니저(운영)로 주입. `.env.example` 참조. 값 자체는 커밋 금지.

| 변수 | 기본값 | 설명 |
|---|---|---|
| DATABASE_URL | postgresql+psycopg2://brain_core_kor:brain_core_kor@localhost:5432/brain_core_kor | DB 연결. AWS 이관 시 RDS URL로 교체 |
| JWT_SECRET | change-me-in-prod | JWT 서명 키 (운영 필수 교체) |
| JWT_USER_MINUTES | 20 | 학부모 토큰 만료(분) |
| JWT_ADMIN_MINUTES | 240 | 관리자 토큰 만료(분) |
| NAME_AES_KEY | (예시 hex) | 이름 AES-256 키, **32바이트 hex(64자)** |
| NAME_HMAC_KEY | (예시 hex) | 이름 조회용 HMAC 키 (hex) |
| STORAGE_BACKEND | local | `local` 만 구현. 이관 시 `s3` 구현 추가 |
| STORAGE_DIR | ./var/uploads | 로컬 업로드 디렉토리 |
| PUBLIC_BASE_URL | /files | 이미지 정적 서빙 경로 prefix |
| MAX_IMAGE_BYTES | 10485760 | 이미지 최대 바이트(초과 시 재압축) |
| IMAGE_MAX_LONG_EDGE | 1280 | 긴 변 최대 px (720p급) |
| MAX_IMAGES_PER_POST | 5 | 게시글당 이미지 수 |
| CORS_ORIGINS | http://localhost:5173 | 허용 오리진(쉼표 구분) |

## 키 생성 예시
```bash
# AES 32바이트 hex
python -c "import os;print(os.urandom(32).hex())"
# HMAC 키
python -c "import os;print(os.urandom(32).hex())"
```

## MCP API 키 발급(현재 수동)
```python
from app.security import hash_api_key
print(hash_api_key("발급할-평문-키"))  # 결과를 admin.api_key_hash 에 저장
```
