<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";

const auth = useAuth();
const router = useRouter();

const mode = ref("user"); // 'user' | 'admin'
const phone = ref("");
const name = ref("");
const pw = ref("");
const loginId = ref("");
const err = ref("");
const loading = ref(false);

async function submit() {
  err.value = "";
  loading.value = true;
  try {
    if (mode.value === "user") {
      await auth.loginUser(phone.value, name.value, pw.value);
    } else {
      await auth.loginAdmin(loginId.value, pw.value);
    }
    if (auth.mustChangePw) router.replace("/change-password");
    else router.replace(auth.isAdmin ? "/admin/lectures" : "/lectures");
  } catch (e) {
    err.value = e.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card" style="max-width:380px;margin:60px auto">
    <h2 style="margin-top:0">TBC 국어관 관리과</h2>
    <div class="field">
      <label>로그인 유형</label>
      <select v-model="mode">
        <option value="user">학부모</option>
        <option value="admin">관리자</option>
      </select>
    </div>

    <template v-if="mode === 'user'">
      <div class="field">
        <label>휴대전화 뒷번호 (4자리)</label>
        <input v-model="phone" maxlength="4" inputmode="numeric" />
      </div>
      <div class="field">
        <label>자녀 이름</label>
        <input v-model="name" />
      </div>
    </template>
    <template v-else>
      <div class="field">
        <label>아이디</label>
        <input v-model="loginId" />
      </div>
    </template>

    <div class="field">
      <label>비밀번호</label>
      <input v-model="pw" type="password" @keyup.enter="submit" />
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <button class="primary" style="width:100%" :disabled="loading" @click="submit">
      {{ loading ? "로그인 중..." : "로그인" }}
    </button>
  </div>
</template>
