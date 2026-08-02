# 알려진 제한사항 (known_limitations.md)

> 작성: Backend | Reviewer·Frontend 참고

## 의도된 미구현(설계상 보류)
- **role/level 권한 차등 미적용** — `require_level()` 골격만 존재(임계값 0, 전부 통과). 운영 시 임계값 지정 필요. (ADR-006)
- **JWT 리프레시 없음** — 만료 시 재로그인. 프론트는 `expires_at`로 사전 안내 권장. (ADR-004)
- **MCP API 키 발급 UI 없음** — 현재 `app.security.hash_api_key`로 수동 발급해 `admin.api_key_hash`에 저장. 키 회전/폐기 절차 미구현.

## 기술적 제한
- **이름 검색은 정확일치만** — 이름이 암호화 저장되어 부분검색 불가. 관리자 사용자 목록의 `name` 필터는 HMAC 정확일치. 부분검색이 필요하면 별도 인덱싱 전략 필요.
- **제목 검색 `ILIKE '%키워드%'`** — 양쪽 와일드카드라 B-tree 인덱스 미사용. 데이터 증가 시 `pg_trgm` GIN 전환 검토(indexes.md).
- **페이징 OFFSET 기반** — 대용량에서 깊은 페이지 느려짐. keyset 페이징 검토.
- **attachment 폴리모픽(FK 없음)** — `(target_type,target_id)` 무결성은 앱에서만 보장. 대상 삭제 시 첨부 정리는 soft delete 흐름에 의존.
- **회차/일련번호 채번** — `pg_advisory_xact_lock` + `MAX+1`. 매우 높은 동시 생성 빈도에서는 락 대기 발생 가능(현 규모 문제없음).
- **이미지 형식** — jpg/jpeg/png 만. HEIC(아이폰) 미지원. 영상 미지원(ADR-005).
- **삭제 정책** — 전 테이블 soft delete. 물리 삭제·보존기간(개인정보) 정책 미구현.

## 운영 전 점검
- `JWT_SECRET`, `NAME_AES_KEY`, `NAME_HMAC_KEY` 실값 교체. **NAME_* 키 분실 시 기존 이름 복호화 불가**(키 백업 필수).
- 시드 `master` 비밀번호 교체.
- 정적 이미지 서빙은 로컬(`/files`) — 운영은 S3/CloudFront로 이전(`StorageBackend` 교체 + main.py mount 제거).
