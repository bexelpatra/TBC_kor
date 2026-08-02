# 상태 관리 (state_management.md)

> 작성: Frontend | Pinia 단일 스토어(auth) + 뷰 로컬 상태

## 전역 상태 — Pinia `useAuth` (stores/auth.js)

| state | 설명 |
|---|---|
| token | JWT 액세스 토큰 (localStorage `brain_core_kor_token` 동기화) |
| actor | `'user'` / `'admin'` (localStorage `brain_core_kor_actor`) |
| displayName | `/me`의 복호화된 표시명 |
| role, level | 관리자 역할/레벨(로그인 응답) |
| expiresAt | 토큰 만료 ISO (localStorage `brain_core_kor_expires`) — SessionTimer가 사용 |
| mustChangePw | 학부모 최초 로그인 변경 강제 플래그 |

**getters**: `isAuthed`, `isAdmin`, `isUser`
**actions**: `loginUser`, `loginAdmin`, `fetchMe`, `changePassword`, `logout`

- 로그인 성공 시 토큰·만료·주체를 저장하고 `fetchMe()`로 표시명 보강.
- 새로고침 시 localStorage에서 토큰/주체/만료 복원(스토어 초기 state). 단 `displayName`은 비어있어 보호 라우트 진입 시 필요하면 `fetchMe()` 재호출 권장(현재는 네비 표시용이라 다음 API 호출로 자연 복구).

## 라우팅 가드 (router/index.js)
1. `meta.public` 아니면 미인증 → `/login`.
2. `mustChangePw` true면 `/change-password` 외 접근 차단.
3. `meta.actor` 와 `auth.actor` 불일치 → 해당 주체 홈으로.

## 세션 만료 처리
- **SessionTimer**가 1초마다 `expiresAt` 비교. 만료 시 `logout()` + `/login` 이동.
- API 호출이 401을 던지면 화면별 `err`에 표시(전역 인터셉터로 자동 로그아웃은 미구현 — 향후 client.js에 401 훅 추가 가능).

## 뷰 로컬 상태 패턴
- 목록 뷰: `items/total/page/size` + 검색 필드. `load()`가 쿼리스트링 구성 → `api.get`. Pager 이벤트로 page/size 갱신 후 재조회.
- 상세/관리 뷰: 엔티티 ref + 폼 ref. 변경 후 `load()` 재호출로 갱신(낙관적 업데이트 미사용 — 단순성 우선).

## 알려진 향후 개선
- 401 전역 처리(자동 로그아웃) 훅.
- 토큰 만료 임박 시 사용자 사전 경고(현재는 타이머 표시만).
- 새로고침 직후 `displayName` 복원을 위한 진입 시 `fetchMe()` 호출.
