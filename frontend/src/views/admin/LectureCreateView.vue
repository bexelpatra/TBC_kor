<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../../api/client";

const router = useRouter();
const lectureAt = ref("");
const subject = ref("");
const err = ref("");

async function create() {
  err.value = "";
  if (!lectureAt.value) { err.value = "일시를 입력하세요"; return; }
  try {
    const l = await api.post("/api/admin/lectures", {
      lecture_at: new Date(lectureAt.value).toISOString(),
      subject: subject.value || null,
    });
    // 생성 후 상세로 이동해 학생·내용·이미지 작성
    router.replace(`/admin/lectures/${l.id}`);
  } catch (e) { err.value = e.message; }
}
</script>

<template>
  <button @click="router.back()">‹ 목록</button>
  <div class="card" style="max-width:480px;margin-top:12px">
    <h2 style="margin-top:0">강의 등록</h2>
    <p class="muted">회차는 자동으로 부여됩니다. 생성 후 학생별 기록과 이미지를 작성합니다.</p>
    <div class="field"><label>일시</label><input type="datetime-local" v-model="lectureAt" /></div>
    <div class="field"><label>주제 (선택)</label><input v-model="subject" placeholder="예: 5월 모의고사 해설" /></div>
    <p v-if="err" class="err">{{ err }}</p>
    <button class="primary" @click="create">생성</button>
  </div>
</template>
