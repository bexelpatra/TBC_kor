# 컴포넌트 맵 (component_map.md)

> 작성: Frontend | 스택: Vue 3 + Vite + Pinia + Vue Router
> 기준: `docs/backend/api_response_examples.md` (가정 아닌 실제 응답 형식)

## 라우트 → 뷰

| 경로 | 뷰 | 주체 | 설명 |
|---|---|---|---|
| `/login` | LoginView | public | 셀렉트(학부모/관리자) + 폼 |
| `/change-password` | ChangePasswordView | auth | 최초/일반 변경(라우터 가드가 최초 변경 강제) |
| `/lectures` | user/LectureListView | user | 본인 특강 목록(검색·페이징) |
| `/lectures/:id` | user/LectureDetailView | user | 상세 + 이미지 + 댓글(작성/수정/삭제·답글 표시) |
| `/notices`, `/notices/:id` | user/NoticeListView, NoticeDetailView | auth | 공지 읽기 |
| `/admin/lectures` | admin/LectureAdminListView | admin | 강의 목록 + 등록 버튼 |
| `/admin/lectures/new` | admin/LectureCreateView | admin | 강의 마스터 생성(→상세로) |
| `/admin/lectures/:id` | admin/LectureAdminDetailView | admin | 학생 추가/내용/이미지/댓글 답글 |
| `/admin/notices` | admin/NoticeAdminView | admin | 공지 CRUD + 이미지 |
| `/admin/users` | admin/UsersView | admin | 사용자 CRUD + 엑셀 양식/일괄 |
| `/admin/comments` | admin/UnansweredView | admin | 미답변 인박스 + 인라인 답글 |

## 공통 컴포넌트
- **App.vue** — 상단 네비(주체별 메뉴), 표시명, `SessionTimer`, 비밀번호/로그아웃.
- **SessionTimer.vue** — `auth.expiresAt` 기반 mm:ss 카운트다운, 만료 시 로그아웃→`/login`.
- **Pager.vue** — 이전/다음 + 페이지 크기 셀렉트(10/20/30). `v-model:page`, `v-model:size`.

## 책임 경계
- **API 호출**: `src/api/client.js` 한 곳. Bearer 자동 첨부, 에러 `{error:{code,message}}` → `Error(message, {code})`. 이미지 URL은 `fileUrl()`로 API 베이스 prefix.
- **인증/세션 상태**: Pinia `stores/auth.js` (토큰 localStorage 유지).
- **격리**: 학부모 화면은 본인 `lecture_user`만 다루는 엔드포인트(`/api/lectures...`)만 호출. 관리자/학부모 라우트는 라우터 가드 `meta.actor`로 분리.
- **날짜**: `util.js` — 저장은 ISO(UTC), 표시는 KST(`fmtDateTime`).

## 빌드 검증
- `npm run build` 통과(46 모듈). dev 서버 포트 5173(백엔드 CORS 허용 오리진과 일치).
