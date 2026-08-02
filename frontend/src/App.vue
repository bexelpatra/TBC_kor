<script setup>
import { useRouter, RouterLink, RouterView } from "vue-router";
import { useAuth } from "./stores/auth";
import { COMMENTS_ENABLED } from "./features";
import SessionTimer from "./components/SessionTimer.vue";

const auth = useAuth();
const router = useRouter();

function logout() {
  auth.logout();
  router.replace("/login");
}
</script>

<template>
  <header v-if="auth.isAuthed" class="row" style="background:#fff;border-bottom:1px solid var(--bd);padding:10px 16px">
    <strong>TBC 국어관</strong>
    <nav class="row" style="margin-left:16px" v-if="auth.isUser">
      <RouterLink to="/lectures">특강</RouterLink>
      <RouterLink to="/notices">공지</RouterLink>
    </nav>
    <nav class="row" style="margin-left:16px" v-else-if="auth.isAdmin">
      <RouterLink to="/admin/lectures">특강관리</RouterLink>
      <RouterLink to="/admin/notices">공지관리</RouterLink>
      <RouterLink to="/admin/users">사용자관리</RouterLink>
      <RouterLink v-if="COMMENTS_ENABLED" to="/admin/comments">미답변</RouterLink>
    </nav>
    <span class="spacer"></span>
    <span class="muted">{{ auth.displayName }}<template v-if="auth.isAdmin"> ({{ auth.role }})</template></span>
    <SessionTimer />
    <RouterLink to="/change-password" class="muted">비밀번호</RouterLink>
    <button @click="logout">로그아웃</button>
  </header>

  <main class="container">
    <RouterView />
  </main>
</template>
