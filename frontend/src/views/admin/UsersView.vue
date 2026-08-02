<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { api } from "../../api/client";
import Pager from "../../components/Pager.vue";

const allItems = ref([]); // 전체 조회 결과 (최대 2000건)
const page = ref(1);
const size = ref(10);
const fPhone = ref("");
const fName = ref("");
const err = ref("");
const sortDir = ref(null); // null | "asc" | "desc" — 이름 정렬

// 단건 추가
const nu = ref({ phone_tail: "", name: "", student_number: "" });
const addErr = ref("");

// 일괄 업로드 결과
const bulk = ref(null);
const uploading = ref(false);

// 이름 수정 팝업
const editing = ref(null); // 수정 대상 사용자 (null 이면 닫힘)
const editName = ref("");
const editErr = ref("");
const saving = ref(false);
const editInput = ref(null);

async function load() {
  try { allItems.value = await api.get("/api/admin/users/all"); }
  catch (e) { err.value = e.message; }
}
function setPage(p) { page.value = p; }
function setSize(s) { size.value = s; page.value = 1; }

function toggleSort() {
  // 클릭할 때마다 기본 → 오름차순 → 내림차순 → 기본 순으로 순환
  sortDir.value = sortDir.value === null ? "asc" : sortDir.value === "asc" ? "desc" : null;
  page.value = 1;
}

// 뒷번호/이름 부분일치 검색 (프론트에서, 입력하는 즉시 반영)
const filteredItems = computed(() => {
  const phone = fPhone.value.trim();
  const name = fName.value.trim();
  return allItems.value.filter(
    (u) => (!phone || u.phone_tail.includes(phone)) && (!name || u.name.includes(name))
  );
});

watch([fPhone, fName], () => { page.value = 1; });

const sortedItems = computed(() => {
  if (!sortDir.value) return filteredItems.value;
  const sorted = [...filteredItems.value].sort((a, b) => a.name.localeCompare(b.name, "ko"));
  return sortDir.value === "desc" ? sorted.reverse() : sorted;
});

const total = computed(() => sortedItems.value.length);

const pagedItems = computed(() => {
  const start = (page.value - 1) * size.value;
  return sortedItems.value.slice(start, start + size.value);
});

async function addUser() {
  addErr.value = "";
  try {
    await api.post("/api/admin/users", { ...nu.value });
    nu.value = { phone_tail: "", name: "", student_number: "" };
    await load();
  } catch (e) { addErr.value = e.message; }
}

function openEdit(u) {
  editing.value = u;
  editName.value = u.name;
  editErr.value = "";
  nextTick(() => editInput.value?.focus());
}

function closeEdit() {
  if (saving.value) return;
  editing.value = null;
}

function onEditBackdrop(e) {
  if (e.target === e.currentTarget) closeEdit();
}

async function saveName() {
  const name = editName.value.trim();
  if (name.length < 2) { editErr.value = "이름은 2자 이상 입력하세요."; return; }
  if (name === editing.value.name) { closeEdit(); return; }
  saving.value = true;
  editErr.value = "";
  try {
    await api.put(`/api/admin/users/${editing.value.id}`, { name });
    await load();
    editing.value = null;
  } catch (e) { editErr.value = e.message; }
  finally { saving.value = false; }
}

async function resetPw(u) {
  if (!confirm(`${u.name} 학생의 비밀번호를 초기화(00+번호)할까요?`)) return;
  try { await api.post(`/api/admin/users/${u.id}/reset-password`); await load(); alert("비밀번호가 초기화되었습니다."); }
  catch (e) { err.value = e.message; }
}

async function removeUser(u) {
  if (!confirm(`${u.name} 학생을 탈퇴 처리할까요?`)) return;
  try { await api.del(`/api/admin/users/${u.id}`); await load(); }
  catch (e) { err.value = e.message; }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

async function downloadTemplate() {
  const blob = await api.download("/api/admin/users/template");
  downloadBlob(blob, "user_template.xlsx");
}

async function downloadBulkReport() {
  const blob = await api.postDownload("/api/admin/users/bulk/report", { results: bulk.value.results });
  downloadBlob(blob, "user_bulk_result.xlsx");
}

async function uploadBulk(e) {
  const file = e.target.files[0];
  if (!file) return;
  err.value = "";
  bulk.value = null;
  uploading.value = true;
  const fd = new FormData();
  fd.append("file", file);
  try { bulk.value = await api.upload("/api/admin/users/bulk", fd); await load(); }
  catch (err2) { err.value = err2.message || "업로드에 실패했습니다."; }
  finally { uploading.value = false; e.target.value = ""; }
}

onMounted(load);
</script>

<template>
  <h2>사용자 관리</h2>

  <div class="card">
    <h3 style="margin-top:0">단건 추가</h3>
    <div class="row">
      <input v-model="nu.phone_tail" maxlength="4" placeholder="뒷번호(4자리)" style="width:130px" />
      <input v-model="nu.name" placeholder="자녀 이름" style="width:160px" />
      <input v-model="nu.student_number" maxlength="4" placeholder="번호 4자리" style="width:130px" />
      <button class="primary" @click="addUser">추가</button>
      <span class="muted">초기 비밀번호 = 00 + 번호 4자리</span>
    </div>
    <p v-if="addErr" class="err">{{ addErr }}</p>
  </div>

  <div class="card" style="margin-top:12px">
    <h3 style="margin-top:0">엑셀 일괄 등록</h3>
    <div class="row">
      <button @click="downloadTemplate" :disabled="uploading">양식 다운로드</button>
      <label class="primary" style="border-radius:6px;padding:6px 12px;border:1px solid var(--pri);background:var(--pri);color:#fff"
             :style="uploading ? 'opacity:.6;cursor:default' : 'cursor:pointer'">
        {{ uploading ? "업로드 중…" : "파일 업로드" }}
        <input type="file" accept=".xlsx" style="display:none" :disabled="uploading" @change="uploadBulk" />
      </label>
      <span v-if="uploading" class="muted">파일을 처리하고 있습니다. 잠시만 기다려 주세요…</span>
    </div>
    <div v-if="bulk" style="margin-top:10px">
      <p>생성 <strong>{{ bulk.created }}</strong>건, 건너뜀 {{ bulk.skipped.length }}건, 오류 {{ bulk.errors.length }}건
        <button @click="downloadBulkReport" style="margin-left:8px">결과 엑셀 다운로드</button>
      </p>
      <ul class="muted">
        <li v-for="s in bulk.skipped" :key="'s'+s.row">행 {{ s.row }}: {{ s.reason }}</li>
        <li v-for="er in bulk.errors" :key="'e'+er.row" class="err">행 {{ er.row }}: {{ er.reason }}</li>
      </ul>
    </div>
  </div>

  <div class="card" style="margin-top:12px">
    <div class="row">
      <input v-model="fPhone" placeholder="뒷번호(일부 가능)" style="width:120px" />
      <input v-model="fName" placeholder="이름(일부 가능)" style="width:150px" />
      <span class="muted">입력하는 즉시 검색됩니다</span>
    </div>
  </div>

  <p v-if="err" class="err">{{ err }}</p>
  <table style="margin-top:12px">
    <thead>
      <tr>
        <th>뒷번호</th>
        <th
          class="sortable-th"
          role="button"
          tabindex="0"
          :aria-sort="sortDir === 'asc' ? 'ascending' : sortDir === 'desc' ? 'descending' : 'none'"
          title="클릭하면 이름 정렬 순서가 바뀝니다 (오름차순 → 내림차순 → 기본)"
          @click="toggleSort"
          @keydown.enter="toggleSort"
          @keydown.space.prevent="toggleSort"
        >
          이름
          <span class="sort-arrow" :class="{ active: sortDir }">{{ sortDir === "desc" ? "▼" : sortDir === "asc" ? "▲" : "⇅" }}</span>
        </th>
        <th>번호</th><th>비번변경</th><th></th><th></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="u in pagedItems" :key="u.id">
        <td>{{ u.phone_tail }}</td>
        <td>
          <span
            class="name-edit"
            role="button"
            tabindex="0"
            title="클릭하면 이름을 수정합니다"
            @click="openEdit(u)"
            @keydown.enter="openEdit(u)"
            @keydown.space.prevent="openEdit(u)"
          >{{ u.name }}</span>
        </td>
        <td>{{ u.student_number }}</td>
        <td>{{ u.must_change_pw ? "필요" : "완료" }}</td>
        <td><button class="outline-pri" @click="resetPw(u)">PW초기화</button></td>
        <td><button class="danger" @click="removeUser(u)">탈퇴</button></td>
      </tr>
      <tr v-if="!pagedItems.length"><td colspan="6" class="muted">등록된 사용자가 없습니다.</td></tr>
    </tbody>
  </table>
  <Pager :total="total" :page="page" :size="size" @update:page="setPage" @update:size="setSize" />

  <Teleport to="body">
    <div v-if="editing" class="ed-overlay" @click="onEditBackdrop" @keydown.esc="closeEdit">
      <div class="ed-box">
        <h3 style="margin-top:0">이름 수정</h3>
        <p class="muted" style="margin-top:0">뒷번호 {{ editing.phone_tail }} · 번호 {{ editing.student_number }}</p>
        <input
          ref="editInput"
          v-model="editName"
          maxlength="20"
          placeholder="새 이름"
          :disabled="saving"
          style="width:100%;box-sizing:border-box"
          @keydown.enter="saveName"
        />
        <p v-if="editErr" class="err">{{ editErr }}</p>
        <div class="ed-actions">
          <button class="primary" :disabled="saving" @click="saveName">{{ saving ? "저장 중…" : "수정" }}</button>
          <button :disabled="saving" @click="closeEdit">취소</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.outline-pri {
  color: var(--pri);
  border-color: var(--pri);
}
.sortable-th {
  cursor: pointer;
  user-select: none;
  padding: 10px 8px;
}
.sortable-th:hover {
  background: #eef2ff;
}
.sortable-th:focus-visible {
  outline: 2px solid var(--pri);
  outline-offset: -2px;
}
.sort-arrow {
  margin-left: 4px;
  font-size: 13px;
  color: var(--muted, #999);
}
.sort-arrow.active {
  color: var(--pri);
}
.name-edit {
  cursor: pointer;
  border-bottom: 1px dashed var(--pri);
  color: var(--pri);
}
.name-edit:focus-visible {
  outline: 2px solid var(--pri);
  outline-offset: 2px;
}
.ed-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ed-box {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  width: 320px;
  max-width: 90vw;
}
.ed-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
