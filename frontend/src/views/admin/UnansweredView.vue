<script setup>
import { ref, onMounted } from "vue";
import { api } from "../../api/client";
import { fmtDateTime } from "../../util";
import Pager from "../../components/Pager.vue";

const items = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const err = ref("");
const replyText = ref({}); // commentId → text

async function load() {
  const q = new URLSearchParams({ page: page.value, size: size.value });
  try { const d = await api.get(`/api/admin/comments/unanswered?${q}`); items.value = d.items; total.value = d.total; }
  catch (e) { err.value = e.message; }
}
function setPage(p) { page.value = p; load(); }
function setSize(s) { size.value = s; page.value = 1; load(); }

async function reply(c) {
  const text = replyText.value[c.id];
  if (!text || !text.trim()) return;
  try { await api.post(`/api/comments/${c.id}/reply`, { content: text }); replyText.value[c.id] = ""; await load(); }
  catch (e) { err.value = e.message; }
}

onMounted(load);
</script>

<template>
  <h2>미답변 댓글</h2>
  <p class="muted">관리자 답글이 아직 없는 학부모 댓글입니다.</p>
  <p v-if="err" class="err">{{ err }}</p>

  <div v-for="c in items" :key="c.id" class="card" style="margin-top:10px">
    <div class="row">
      <span class="muted">{{ fmtDateTime(c.created_at) }}</span>
      <RouterLink :to="`/admin/lectures`" class="muted">기록 #{{ c.lecture_user_id }}</RouterLink>
    </div>
    <p style="white-space:pre-wrap">{{ c.content }}</p>
    <div class="row">
      <input v-model="replyText[c.id]" placeholder="답글 입력" style="flex:1" @keyup.enter="reply(c)" />
      <button class="primary" @click="reply(c)">답글</button>
    </div>
  </div>
  <div v-if="!items.length" class="card muted" style="margin-top:10px">미답변 댓글이 없습니다.</div>
  <Pager :total="total" :page="page" :size="size" @update:page="setPage" @update:size="setSize" />
</template>
