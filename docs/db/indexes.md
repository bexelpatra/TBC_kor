# 인덱스 전략 (indexes.md)

> 작성: DB | 모든 유니크는 soft delete와 공존하도록 **부분 인덱스(`WHERE deleted_at IS NULL`)**.

| 인덱스 | 테이블 | 컬럼 | 종류 | 이유 |
|---|---|---|---|---|
| uq_app_user_login | app_user | (phone_tail, name_hash) | 부분 유니크 | user 로그인 조회 키 + 중복 가입 방지 |
| uq_admin_login_id | admin | (login_id) | 부분 유니크 | admin 로그인 + 중복 방지 |
| uq_lecture_round | lecture | (round_no) | 부분 유니크 | 회차 자동 채번 유일성 |
| ix_lecture_at | lecture | (lecture_at) | 일반 | 날짜 범위 검색·정렬 |
| uq_lecture_user | lecture_user | (lecture_id, user_id) | 부분 유니크 | 강의당 학생 1행 |
| ix_lecture_user_user | lecture_user | (user_id) | 부분 | **학부모 격리 조회** 핵심 — 가장 빈번 |
| ix_lecture_user_title | lecture_user | (title) | 일반 | 제목 검색 |
| ix_attachment_target | attachment | (target_type, target_id) | 부분 | 게시글/공지별 첨부 조회 |
| ix_comment_lecture_user | comment | (lecture_user_id) | 부분 | 기록별 댓글 조회 |
| ix_comment_parent | comment | (parent_id) | 일반 | 답글 조회 + 미답변 판정 |
| uq_notice_serial | notice | (serial_no) | 부분 유니크 | 일련번호 유일성 |
| ix_notice_at | notice | (notice_at) | 일반 | 날짜 검색·정렬 |

## 검토 포인트 (향후)
- **제목 검색**이 `LIKE '%키워드%'`(양쪽 와일드카드)면 일반 B-tree 인덱스는 무력 → 데이터 증가 시 `pg_trgm` GIN 인덱스(`ix_lecture_user_title`) 전환 검토.
- **미답변 댓글 인박스**가 느려지면 `comment (lecture_user_id) WHERE author_type='user' AND parent_id IS NULL` 형태의 부분 인덱스 추가 검토.
- 페이징은 OFFSET 기반(초기). 대용량 시 keyset(커서) 페이징 검토.
