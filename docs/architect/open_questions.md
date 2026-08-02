# 미결 사항 · 가정 (open_questions.md)

> 작성: Architect | 다음 에이전트가 시작하기 전 확인 권장

## 결정 완료 (2026-06-01)

1. **user 초기 비밀번호** — `00`+YYMM(예: 0503→`000503`) + `must_change_pw`로 최초 로그인 시 변경 강제. ✅
2. **회차/일련번호** — 시스템 자동 채번(직전 최대값+1). ✅
3. **admin 계정 프로비저닝** — 시드 계정 `master` 1개(비밀번호는 `MASTER_ADMIN_PASSWORD` 환경변수로 주입), 이후 관리자가 추가. 자가가입 없음. ✅
4. **admin 이름 암호화** — 미적용(평문). id/pw/이름은 개인정보 아님, 비밀번호만 bcrypt 해시. ✅

## 확인 필요 (사용자 결정 대기)

5. **뒷번호 추가 보호** — 현재 평문 저장(조회 키, 4자리라 식별성 낮음). 추가 보호 필요 시 HMAC 검토.

## 가정 (별도 이견 없으면 확정)

- HEIC(아이폰 사진) 업로드는 현재 미지원. 추후 `HEIC→JPEG` 자동 변환 옵션 검토.
- role/level 권한 차등은 골격만, 임계값 전부 통과(현재 권한 분기는 user/admin 2종만).
- JWT 슬라이딩 갱신 없음. 만료 시 재로그인.
- 검색: 날짜 범위 + 제목 부분일치, 정렬 최신순, 페이징 LIMIT/OFFSET.
- 이미지: lecture_user/notice당 최대 5장, jpg/jpeg/png, 10MB 초과 시 긴 변 1280px(720p급) 재압축.

## 이관(AWS) 시 구체화 필요

- 컴퓨팅: EC2 / ECS(Fargate) / Lambda 중 선택.
- 파일: S3 + (필요 시) CloudFront. Storage 구현체 교체.
- 시크릿: AES·HMAC 키, DB 자격, API 키 → KMS/Secrets Manager.
- 프론트 배포: S3 정적 호스팅 + CloudFront vs 동일 서버 서빙.

## 기한
- 미정. 우선순위·마일스톤 합의 필요.
