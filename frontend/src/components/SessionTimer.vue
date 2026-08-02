<script setup>
// 남은 로그인 시간 표시. 만료되면 로그아웃 → 로그인 이동.
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";

const auth = useAuth();
const router = useRouter();
const label = ref("");
let timer = null;

function tick() {
  if (!auth.expiresAt) return;
  const left = Math.floor((new Date(auth.expiresAt).getTime() - Date.now()) / 1000);
  if (left <= 0) {
    label.value = "만료됨";
    auth.logout();
    router.replace("/login");
    return;
  }
  const m = String(Math.floor(left / 60)).padStart(2, "0");
  const s = String(left % 60).padStart(2, "0");
  label.value = `${m}:${s}`;
}

onMounted(() => {
  tick();
  timer = setInterval(tick, 1000);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <span class="muted" title="남은 로그인 시간">⏱ {{ label }}</span>
</template>
