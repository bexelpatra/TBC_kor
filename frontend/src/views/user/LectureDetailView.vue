<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, fileUrl } from "../../api/client";
import { fmtDateTime } from "../../util";
import { COMMENTS_ENABLED } from "../../features";

const route = useRoute();
const router = useRouter();
const lu = ref(null);
const comments = ref([]);
const newComment = ref("");
const editId = ref(null);
const editText = ref("");
const err = ref("");

const luId = route.params.id;

// 부모 댓글 + 그에 달린 관리자 답글 묶기
const threads = computed(() => {
  const parents = comments.value.filter((c) => !c.parent_id);
  return parents.map((p) => ({
    ...p,
    reply: comments.value.find((c) => c.parent_id === p.id) || null,
  }));
});

async function load() {
  err.value = "";
  try {
    lu.value = await api.get(`/api/lectures/${luId}`);
    if (COMMENTS_ENABLED) comments.value = await api.get(`/api/lectures/${luId}/comments`);
  } catch (e) { err.value = e.message; }
}

async function addComment() {
  if (!newComment.value.trim()) return;
  try {
    await api.post(`/api/lectures/${luId}/comments`, { content: newComment.value });
    newComment.value = "";
    await load();
  } catch (e) { err.value = e.message; }
}

function startEdit(c) { editId.value = c.id; editText.value = c.content; }
async function saveEdit() {
  try {
    await api.put(`/api/comments/${editId.value}`, { content: editText.value });
    editId.value = null;
    await load();
  } catch (e) { err.value = e.message; }
}
async function removeComment(c) {
  if (!confirm("댓글을 삭제할까요?")) return;
  try { await api.del(`/api/comments/${c.id}`); await load(); }
  catch (e) { err.value = e.message; }
}

onMounted(load);
</script>

<template>
  <button @click="router.back()">‹ 목록</button>
  <p v-if="err" class="err">{{ err }}</p>

  <div v-if="lu" class="card" style="margin-top:12px">
    <div class="row"><span class="tag">{{ lu.round_no }}회차</span><span class="muted">{{ fmtDateTime(lu.lecture_at) }}</span></div>
    <h2 style="margin:8px 0">{{ lu.title }}</h2>
    <p style="white-space:pre-wrap">{{ lu.content }}</p>
    <div v-for="img in lu.images" :key="img.id">
      <img :src="fileUrl(img.url)" class="thumb" />
    </div>
  </div>

  <div v-if="COMMENTS_ENABLED" class="card" style="margin-top:16px">
    <h3 style="margin-top:0">댓글</h3>
    <div v-for="t in threads" :key="t.id" style="border-bottom:1px solid var(--bd);padding:10px 0">
      <template v-if="editId === t.id">
        <textarea v-model="editText" rows="2" style="width:100%"></textarea>
        <div class="row" style="margin-top:6px">
          <button class="primary" @click="saveEdit">저장</button>
          <button @click="editId = null">취소</button>
        </div>
      </template>
      <template v-else>
        <div class="row"><strong>나</strong><span class="spacer"></span>
          <template v-if="!t.reply">
            <button @click="startEdit(t)">수정</button>
            <button class="danger" @click="removeComment(t)">삭제</button>
          </template>
        </div>
        <p style="margin:6px 0;white-space:pre-wrap">{{ t.content }}</p>
      </template>

      <div v-if="t.reply" style="margin:8px 0 0 16px;padding:10px;background:#f0f4ff;border-radius:8px">
        <strong class="tag">관리자 답글</strong>
        <p style="margin:6px 0 0;white-space:pre-wrap">{{ t.reply.content }}</p>
      </div>
    </div>
    <div v-if="!threads.length" class="muted">아직 댓글이 없습니다.</div>

    <div style="margin-top:14px">
      <textarea v-model="newComment" rows="2" style="width:100%" placeholder="댓글을 입력하세요"></textarea>
      <button class="primary" style="margin-top:6px" @click="addComment">댓글 작성</button>
    </div>
  </div>
</template>
