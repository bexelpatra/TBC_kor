import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../stores/auth";
import { COMMENTS_ENABLED } from "../features";

const routes = [
  { path: "/login", component: () => import("../views/LoginView.vue"), meta: { public: true } },
  { path: "/change-password", component: () => import("../views/ChangePasswordView.vue") },

  // user (학부모)
  { path: "/", redirect: "/lectures" },
  { path: "/lectures", component: () => import("../views/user/LectureListView.vue"), meta: { actor: "user" } },
  { path: "/lectures/:id", component: () => import("../views/user/LectureDetailView.vue"), meta: { actor: "user" } },
  { path: "/notices", component: () => import("../views/user/NoticeListView.vue") },
  { path: "/notices/:id", component: () => import("../views/user/NoticeDetailView.vue") },

  // admin
  { path: "/admin/users", component: () => import("../views/admin/UsersView.vue"), meta: { actor: "admin" } },
  { path: "/admin/lectures", component: () => import("../views/admin/LectureAdminListView.vue"), meta: { actor: "admin" } },
  { path: "/admin/lectures/new", component: () => import("../views/admin/LectureCreateView.vue"), meta: { actor: "admin" } },
  { path: "/admin/lectures/:id", component: () => import("../views/admin/LectureAdminDetailView.vue"), meta: { actor: "admin" } },
  { path: "/admin/notices", component: () => import("../views/admin/NoticeAdminView.vue"), meta: { actor: "admin" } },
  { path: "/admin/comments", component: () => import("../views/admin/UnansweredView.vue"), meta: { actor: "admin", feature: "comments" } },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to) => {
  const auth = useAuth();
  if (to.meta.public) return true;
  if (!auth.isAuthed) return "/login";
  // 비활성화된 기능(댓글) 라우트 직접 접근 차단
  if (to.meta.feature === "comments" && !COMMENTS_ENABLED) {
    return auth.isAdmin ? "/admin/lectures" : "/lectures";
  }
  // 최초 비밀번호 변경 강제 (user)
  if (auth.mustChangePw && to.path !== "/change-password") return "/change-password";
  // 주체 권한 체크
  if (to.meta.actor && to.meta.actor !== auth.actor) {
    return auth.isAdmin ? "/admin/lectures" : "/lectures";
  }
  return true;
});

export default router;
