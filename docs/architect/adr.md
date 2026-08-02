# Architecture Decision Records (adr.md)

> 작성: Architect

---

## ADR-001: 특강을 `lecture`(마스터) + `lecture_user`(학생별 기록)로 분리
- 상태: 수락됨
- 배경: 한 특강에 여러 학생이 참여하지만, 학생마다 내용·이미지·댓글이 다르고 학부모 간 절대 격리가 필요.
- 결정: `lecture`(일시·회차·담당 강사) 1:N `lecture_user`(학생별 제목·내용). `lecture ↔ user`는 `lecture_user`를 연결 객체로 하는 N:N. 이미지·댓글은 `lecture_user`에 종속.
- 영향: 학부모 조회는 항상 `lecture_user.user_id = 본인`으로 스코핑 → 다른 학부모 데이터에 쿼리 자체가 닿지 않아 격리가 구조적으로 보장됨.

## ADR-002: DB는 PostgreSQL
- 상태: 수락됨
- 배경: 로컬 Linux 테스트 후 AWS RDS 이관 예정.
- 결정: 처음부터 PostgreSQL 사용(로컬은 도커/네이티브). ORM=SQLAlchemy, 마이그레이션=Alembic.
- 영향: 이관 시 SQL/타입 재작업 최소화.

## ADR-003: 이름 AES 암호화 + 조회용 HMAC
- 상태: 수락됨
- 배경: 미성년자 이름 등 개인정보 보호. 단 로그인은 이름으로 행을 찾아야 함(암호문은 검색 불가).
- 결정: **user 이름만** `name_enc`(AES, 표시용) + `name_hash`(HMAC-SHA256, 조회·유니크용) 분리 저장. 로그인은 `뒷번호 + name_hash`로 조회 후 비밀번호 검증. **admin은 id/pw/이름이 개인정보가 아니므로 이름은 평문, 비밀번호만 bcrypt 해시.**
- 영향: 키 2종(암호화·HMAC)을 시크릿으로 관리. AWS 이관 시 KMS/Secrets Manager.

## ADR-004: JWT, 리프레시 토큰 없음
- 상태: 수락됨
- 결정: 액세스 토큰만 사용. user 20분 / admin 4시간 만료. user·admin 공통으로 남은 시간 표시 UI 제공.
- 영향: 만료 시 재로그인. 슬라이딩 갱신 없음(보안 우선). 향후 필요 시 재검토.

## ADR-005: 첨부는 폴리모픽 `attachment` 단일 테이블(이미지 전용)
- 상태: 수락됨
- 배경: 특강·공지 양쪽에 이미지 첨부 필요. 영상은 제외.
- 결정: `attachment(target_type, target_id, ...)`로 `lecture_user`·`notice` 공용. jpg/jpeg/png, 게시글당 5장, 10MB 초과 시 720p 재압축.
- 영향: 저장 추상화 한 곳에서 처리. `image_files`의 `order`는 예약어라 `display_order`로 명명.

## ADR-006: role/level 권한은 검사 골격만, 임계값 전부 통과
- 상태: 수락됨
- 배경: 권한 차등은 추후. 그러나 구조는 미리 마련.
- 결정: 백엔드 `require_level(n)` 의존성 + 프론트 라우트 가드 스캐폴딩. 현재 임계값은 모두 0(전부 통과). role(강사>보조자>관리자), level(1~10) 컬럼만 저장.
- 영향: 추후 임계값만 조정하면 권한 차등 활성화.

## ADR-007: 파일 저장소 추상화 (로컬 → S3)
- 상태: 수락됨
- 결정: `Storage` 인터페이스(save/load/delete/url) 뒤에 로컬 FS 구현. AWS 이관 시 S3 구현으로 교체. DB에는 키/상대경로만 저장.
- 영향: 이관 시 애플리케이션 로직 변경 없이 구현체 교체.

## ADR-008: MCP는 관리자 전용·읽기 전용·API 키 인증
- 상태: 수락됨
- 결정: 특강·공지 조회/검색만 노출. 관리자별 API 키로 인증(20분 JWT와 분리). 쓰기 없음.
- 영향: AI 클라이언트가 단명 JWT 없이 안정적으로 조회 가능. 키 유출 대비 폐기/회전 고려.

## ADR-009: user 비밀번호는 6자리 숫자, 초기값 `00`+YYMM
- 상태: 수락됨
- 결정: 복잡도=6자리 숫자(bcrypt 해시). 등록 시 초기값 = `00` + 출생 YYMM(예: 0503 → `000503`), `must_change_pw=true`로 최초 로그인 시 변경 강제.
- 영향: 발급 절차 단순. 변경 전 계정은 취약하므로 최초 변경 강제가 필수.

## ADR-010: 회차/일련번호 자동 채번
- 상태: 수락됨
- 결정: `lecture.round_no`, `notice.serial_no`는 직전 최대값+1로 시스템 자동 채번(관리자 입력 아님).
- 영향: 동시 등록 시 채번 경합 가능 → 트랜잭션/시퀀스 또는 잠금으로 유일성 보장(DB 에이전트가 구체화).

## ADR-011: 최초 관리자 시드 계정
- 상태: 수락됨
- 결정: 시드 스크립트로 `master` 계정 1개 생성. 비밀번호는 환경변수 `MASTER_ADMIN_PASSWORD`로 주입하고 bcrypt 해시로 저장한다(문서·코드에 평문 기록 금지). 나머지 필드 임의. 이후 관리자는 관리자가 추가.
- 영향: 부트스트랩 이후 시드 계정 비밀번호 교체 권장.

## ADR-012: 운영 배포는 단일 VM + docker-compose (매니지드 분리 보류)
- 상태: 수락됨
- 배경: 사용자 200~1000명, 트래픽 ~3만 건/일(평균 0.35 req/s)의 소규모. RDS+App Runner+CloudFront를 따로 상시 가동하면 idle 비용이 누적되어 월 $35~90이 됨. 이 규모엔 매니지드 분리의 값어치(자동 백업·페일오버)보다 비용·운영 복잡도가 큼.
- 결정: 단일 VM(EC2 t4g.small 또는 Lightsail 2GB) 1대에 docker-compose로 FastAPI + PostgreSQL + Caddy(리버스 프록시·자동 TLS)를 함께 구동. 이미지는 S3/Cloudflare R2, 프론트는 Cloudflare Pages(무료). DB 백업은 `pg_dump`→오브젝트 스토리지 cron으로 대체. 상세는 `/docs/deploy/deployment_plan.md`.
- 영향: 월 ~$10~12 고정 비용. RDS 자동 백업·페일오버를 직접 구성해야 함(이 규모 허용). 부하 증가 시 DB만 RDS로 분리하는 확장 경로 유지(스토리지 추상화·env 주입 덕에 코드 변경 최소).

## ADR-013: 이미지 저장소는 1단계 로컬(VM 디스크), 동작 확인 후 S3 전환 검토
- 상태: 수락됨 (ADR-012의 이미지 저장소 결정을 구체화/대체)
- 배경: Lightsail 2GB 플랜에 ~60GB SSD가 포함되어 있고, 이미지 정책(jpg/png, 10MB 제한, 5장/포스트, 사용자 200~1000명) 기준 누적량이 수 GB 수준 → 1단계에서 S3 도입 비용·작업이 불필요. `storage.py`에 `LocalStorage`가 이미 구현돼 있어 추가 코드 작업 없이 바로 사용 가능.
- 결정: `STORAGE_BACKEND=local`로 배포, `backend/var/uploads`를 docker volume으로 영속화. `backup.sh`에서 DB(`pg_dump`)와 함께 uploads 디렉토리도 압축해 백업용 S3/R2 버킷에 업로드(이미지도 백업 대상에 포함). 운영 동작 확인 후, 디스크 용량/CDN 필요성에 따라 `S3Storage` 구현 + 기존 이미지 마이그레이션으로 2단계 전환.
- 영향: 1단계 비용 절감(이미지용 버킷 불필요, 백업용 버킷만 운용) 및 구현 범위 축소. 단, VM 디스크 용량을 모니터링해야 하고, 이미지 접근은 API(`/files`)를 경유(2단계 전환 전까지 별도 CDN 없음). 상세는 `/docs/deploy/deployment_plan.md`.
