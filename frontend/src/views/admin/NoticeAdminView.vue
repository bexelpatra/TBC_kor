<script setup>
import { ref, onMounted } from "vue";
import { api, fileUrl } from "../../api/client";
import { fmtDateTime } from "../../util";
import Pager from "../../components/Pager.vue";

const items = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const err = ref("");

const form = ref({ id: null, notice_at: "", title: "", content: "", images: [] });
const newFiles = ref([]); // 신규 작성 시 첨부할 이미지 (생성 후 업로드)

// datetime-local 입력용 현재 시각 문자열
function nowLocal() {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

async function load() {
  const q = new URLSearchParams({ page: page.value, size: size.value });
  try { const d = await api.get(`/api/notices?${q}`); items.value = d.items; total.value = d.total; }
  catch (e) { err.value = e.message; }
}
function setPage(p) { page.value = p; load(); }
function setSize(s) { size.value = s; page.value = 1; load(); }

// 행 클릭 → 카드에 조회/수정
function edit(n) {
  const dt = new Date(n.notice_at);
  const local = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  form.value = { id: n.id, notice_at: local, title: n.title, content: n.content || "", images: n.images || [] };
}
// 신규 추가 / 취소 — 일시는 현재 시각 기본값
function reset() { form.value = { id: null, notice_at: nowLocal(), title: "", content: "", images: [] }; newFiles.value = []; }
function pickNewFiles(e) { newFiles.value = [...e.target.files]; }

async function save() {
  err.value = "";
  if (!form.value.title) { err.value = "제목을 입력하세요"; return; }
  try {
    const body = { title: form.value.title, content: form.value.content || null };
    if (form.value.id) {
      await api.put(`/api/admin/notices/${form.value.id}`, body);
    } else {
      if (!form.value.notice_at) { err.value = "일시를 입력하세요"; return; }
      const created = await api.post("/api/admin/notices", { ...body, notice_at: new Date(form.value.notice_at).toISOString() });
      // 신규 작성에 첨부한 이미지가 있으면 생성된 공지에 업로드
      if (newFiles.value.length) {
        const fd = new FormData(); newFiles.value.forEach((f) => fd.append("files", f));
        await api.upload(`/api/admin/notices/${created.id}/images`, fd);
      }
    }
    reset(); await load();
  } catch (e) { err.value = e.message; }
}

async function remove() {
  if (!form.value.id) return;
  if (!confirm("공지를 삭제할까요?")) return;
  await api.del(`/api/admin/notices/${form.value.id}`); reset(); await load();
}

// 선택된 공지에 이미지 추가 (저장된 공지에만 가능)
async function uploadImg(e) {
  if (!form.value.id) return;
  const files = [...e.target.files];
  if (!files.length) return;
  const fd = new FormData(); files.forEach((f) => fd.append("files", f));
  try {
    await api.upload(`/api/admin/notices/${form.value.id}/images`, fd);
    await load();
    const cur = items.value.find((x) => x.id === form.value.id);
    if (cur) form.value.images = cur.images; // 카드 썸네일 갱신
  } catch (er) { err.value = er.message; }
  e.target.value = "";
}

onMounted(() => { reset(); load(); });
</script>

<template>
  <h2>공지 관리</h2>
  <div class="card" :style="{ background: form.id ? '' : '#e8f7ea' }">
    <div class="row">
      <h3 style="margin:0">{{ form.id ? "공지 수정" : "공지 작성 (신규)" }}</h3>
      <span class="spacer"></span>
      <button @click="reset">신규 추가</button>
    </div>
    <div class="field" v-if="!form.id"><label>일시</label><input type="datetime-local" v-model="form.notice_at" /></div>
    <div class="field"><label>제목</label><input v-model="form.title" /></div>
    <div class="field"><label>내용</label><textarea v-model="form.content" rows="3"></textarea></div>

    <div v-if="form.id && form.images.length" class="row">
      <img v-for="img in form.images" :key="img.id" :src="fileUrl(img.url)" style="width:100px;border-radius:6px;border:1px solid var(--bd)" />
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <div class="row">
      <button class="primary" @click="save">{{ form.id ? "수정" : "작성" }}</button>
      <!-- 수정 모드: 즉시 업로드 / 신규 모드: 작성 시 함께 업로드 -->
      <label v-if="form.id" style="border:1px solid var(--bd);border-radius:6px;padding:6px 10px;cursor:pointer">이미지 추가
        <input type="file" accept=".jpg,.jpeg,.png" multiple style="display:none" @change="uploadImg" /></label>
      <template v-else>
        <label style="border:1px solid var(--bd);border-radius:6px;padding:6px 10px;cursor:pointer">이미지 추가
          <input type="file" accept=".jpg,.jpeg,.png" multiple style="display:none" @change="pickNewFiles" /></label>
        <span v-if="newFiles.length" class="muted">{{ newFiles.length }}개 선택됨</span>
      </template>
      <button v-if="form.id" class="danger" @click="remove">삭제</button>
      <button v-if="form.id" @click="reset">취소</button>
    </div>
  </div>

  <table style="margin-top:12px">
    <thead><tr><th style="width:50px">번호</th><th>제목</th><th style="width:160px">일시</th></tr></thead>
    <tbody>
      <tr v-for="n in items" :key="n.id" @click="edit(n)" style="cursor:pointer"
          :style="{ background: form.id === n.id ? '#eef4ff' : '' }">
        <td>{{ n.serial_no }}</td>
        <td>{{ n.title }}<span v-if="n.images.length" class="muted"> 📷{{ n.images.length }}</span></td>
        <td>{{ fmtDateTime(n.notice_at) }}</td>
      </tr>
      <tr v-if="!items.length"><td colspan="3" class="muted">공지가 없습니다.</td></tr>
    </tbody>
  </table>
  <Pager :total="total" :page="page" :size="size" @update:page="setPage" @update:size="setSize" />
</template>
