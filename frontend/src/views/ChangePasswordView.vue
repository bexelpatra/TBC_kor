<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";

const auth = useAuth();
const router = useRouter();
const current = ref("");
const next = ref("");
const next2 = ref("");
const err = ref("");
const ok = ref(false);

async function submit() {
  err.value = "";
  if (next.value !== next2.value) { err.value = "새 비밀번호가 일치하지 않습니다"; return; }
  try {
    await auth.changePassword(current.value, next.value);
    ok.value = true;
    setTimeout(() => router.replace(auth.isAdmin ? "/admin/lectures" : "/lectures"), 800);
  } catch (e) {
    err.value = e.message;
  }
}
</script>

<template>
  <div class="card" style="max-width:400px;margin:40px auto">
    <h2 style="margin-top:0">비밀번호 변경</h2>
    <p v-if="auth.mustChangePw" class="muted">최초 로그인입니다. 비밀번호를 변경해주세요.</p>
    <p class="muted" v-if="auth.isUser">학부모 비밀번호는 6자리 숫자입니다.</p>
    <p class="muted" v-else>관리자 비밀번호는 영문·숫자 혼합 8자 이상입니다.</p>

    <div class="field"><label>현재 비밀번호</label><input v-model="current" type="password" /></div>
    <div class="field"><label>새 비밀번호</label><input v-model="next" type="password" :maxlength="auth.isUser ? 6 : undefined" /></div>
    <div class="field"><label>새 비밀번호 확인</label><input v-model="next2" type="password" :maxlength="auth.isUser ? 6 : undefined" /></div>

    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="ok" style="color:green">변경되었습니다.</p>
    <button class="primary" @click="submit">변경</button>
  </div>
</template>
