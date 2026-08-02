<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, fileUrl } from "../../api/client";
import { fmtDateTime } from "../../util";
import { COMMENTS_ENABLED } from "../../features";
import ImageLightbox from "../../components/ImageLightbox.vue";

const lbVisible = ref(false);
const lbImages = ref([]);
const lbStart = ref(0);
function openLightbox(images, idx) {
  lbImages.value = images.map((img) => fileUrl(img.url));
  lbStart.value = idx;
  lbVisible.value = true;
}

const route = useRoute();
const router = useRouter();
const lectureId = route.params.id;

const lecture = ref(null);
const students = ref([]); // lecture_user 목록 (+ comments 로드)
const err = ref("");

// 학생 추가
const userQuery = ref("");
const candidates = ref([]);
const picked = ref(null);
const stTitle = ref("");
const stContent = ref("");
const stFiles = ref([]); // 학생 기록 생성 시 첨부할 이미지 (생성 후 업로드)

async function load() {
  err.value = "";
  try {
    lecture.value = await api.get(`/api/admin/lectures/${lectureId}`);
    const rows = await api.get(`/api/admin/lectures/${lectureId}/students`);
    students.value = rows.map((r) => ({ ...r, studentName: r.student_name, phoneTail: r.phone_tail || "", comments: [], showComments: false, carouselIdx: 0 }));
    // 댓글 개수 표기를 위해 각 학생 기록의 댓글을 미리 로드 (기본은 숨김)
    if (COMMENTS_ENABLED) {
      for (const lu of students.value) lu.comments = await api.get(`/api/admin/lecture-users/${lu.id}/comments`);
    }
  } catch (e) { err.value = e.message; }
}

async function searchUsers() {
  const q = new URLSearchParams({ size: 10 });
  if (/^\d+$/.test(userQuery.value)) q.set("phone_tail", userQuery.value);
  else q.set("name", userQuery.value);
  const d = await api.get(`/api/admin/users?${q}`);
  candidates.value = d.items;
  // 새 검색 시 하위 입력(대상/제목/내용/첨부) 초기화
  picked.value = null; stTitle.value = ""; stContent.value = ""; stFiles.value = [];
}

// 생성 폼의 파일 선택 보관
function pickFiles(e) { stFiles.value = [...e.target.files]; }

async function addStudent() {
  if (!picked.value || !stTitle.value) { err.value = "학생과 제목을 입력하세요"; return; }
  try {
    const created = await api.post(`/api/admin/lectures/${lectureId}/students`, [
      { app_user_id: picked.value.id, title: stTitle.value, content: stContent.value || null },
    ]);
    // 기록 생성 후, 첨부한 이미지가 있으면 새 lecture_user에 업로드
    for (const lu of created) {
      let images = lu.images || [];
      if (stFiles.value.length) {
        const fd = new FormData();
        stFiles.value.forEach((f) => fd.append("files", f));
        images = await api.upload(`/api/admin/lecture-users/${lu.id}/images`, fd);
      }
      students.value.push({ ...lu, images, comments: [], showComments: false, carouselIdx: 0, studentName: picked.value.name, phoneTail: picked.value.phone_tail || "" });
    }
    picked.value = null; stTitle.value = ""; stContent.value = ""; stFiles.value = [];
    userQuery.value = ""; candidates.value = [];
  } catch (e) { err.value = e.message; }
}

async function uploadImages(lu, e) {
  const files = [...e.target.files];
  if (!files.length) return;
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  try { lu.images = await api.upload(`/api/admin/lecture-users/${lu.id}/images`, fd); lu.carouselIdx = lu.images.length - 1; }
  catch (er) { err.value = er.message; }
  e.target.value = "";
}

async function loadComments(lu) {
  lu.comments = await api.get(`/api/admin/lecture-users/${lu.id}/comments`);
}
async function reply(lu, parent) {
  const text = prompt("답글 내용");
  if (!text) return;
  try { await api.post(`/api/comments/${parent.id}/reply`, { content: text }); await loadComments(lu); }
  catch (e) { err.value = e.message; }
}
async function delStudent(lu) {
  if (!confirm("이 학생 기록을 삭제할까요?")) return;
  await api.del(`/api/admin/lecture-users/${lu.id}`);
  students.value = students.value.filter((s) => s.id !== lu.id);
}
async function delLecture() {
  if (!confirm("강의(및 전체 기록)를 삭제할까요?")) return;
  await api.del(`/api/admin/lectures/${lectureId}`);
  router.replace("/admin/lectures");
}

function topComments(lu) { return (lu.comments || []).filter((c) => !c.parent_id); }
function replyOf(lu, c) { return (lu.comments || []).find((r) => r.parent_id === c.id); }

onMounted(load);
</script>

<template>
  <button @click="router.push('/admin/lectures')">‹ 목록</button>
  <p v-if="err" class="err">{{ err }}</p>

  <div v-if="lecture" class="card" style="margin-top:12px">
    <div class="row">
      <span class="tag">{{ lecture.round_no }}회차</span>
      <span class="muted">{{ fmtDateTime(lecture.lecture_at) }}</span>
      <span class="spacer"></span>
      <button class="danger" @click="delLecture">강의 삭제</button>
    </div>
    <h2 style="margin:8px 0">{{ lecture.subject || "(주제 없음)" }}</h2>
  </div>

  <div class="card" style="margin-top:12px">
    <h3 style="margin-top:0">학생 기록 추가</h3>
    <div class="row">
      <input v-model="userQuery" placeholder="학생 이름 또는 뒷번호" @keyup.enter="searchUsers" />
      <button @click="searchUsers">학생 검색</button>
    </div>
    <div class="row" v-if="candidates.length" style="margin-top:6px">
      <button v-for="c in candidates" :key="c.id" :class="{ primary: picked && picked.id === c.id }" @click="picked = c">
        {{ c.name }} ({{ c.phone_tail }})
      </button>
    </div>
    <div v-if="picked" style="margin-top:10px">
      <div class="field"><label>대상: <strong>{{ picked.name }}</strong></label></div>
      <div class="field"><label>제목 (필수)</label><input v-model="stTitle" /></div>
      <div class="field"><label>내용</label><textarea v-model="stContent" rows="3"></textarea></div>
      <div class="field">
        <label>이미지 첨부 (jpg/jpeg/png)</label>
        <input type="file" accept=".jpg,.jpeg,.png" multiple @change="pickFiles" />
        <span v-if="stFiles.length" class="muted">{{ stFiles.length }}개 선택됨</span>
      </div>
      <button class="primary" @click="addStudent">학생 기록 생성</button>
    </div>
  </div>

  <div v-for="(lu, idx) in students" :key="lu.id" class="card" style="margin-top:12px">
    <div class="row">
      <strong>{{ idx + 1 }}. {{ lu.studentName }}({{ lu.phoneTail }})</strong><span class="muted">{{ lu.title }}</span>
      <span v-if="lu.created_at" class="muted">· 작성 {{ fmtDateTime(lu.created_at) }}</span>
      <span class="spacer"></span>
      <label style="border:1px solid var(--bd);border-radius:6px;padding:6px 10px;cursor:pointer">
        이미지 추가<input type="file" accept=".jpg,.jpeg,.png" multiple style="display:none" @change="(e) => uploadImages(lu, e)" />
      </label>
      <button v-if="COMMENTS_ENABLED" @click="lu.showComments = !lu.showComments">
        {{ lu.showComments ? "댓글 숨기기" : (topComments(lu).length ? topComments(lu).length + "개의 댓글" : "댓글 없음") }}
      </button>
      <button class="danger" @click="delStudent(lu)">삭제</button>
    </div>
    <p v-if="lu.content" style="white-space:pre-wrap">{{ lu.content }}</p>
    <div v-if="lu.images && lu.images.length" class="carousel">
      <button class="carousel-btn" :disabled="lu.carouselIdx === 0" @click="lu.carouselIdx--">&lsaquo;</button>
      <img :src="fileUrl(lu.images[lu.carouselIdx].url)" class="carousel-img" @click="openLightbox(lu.images, lu.carouselIdx)" />
      <button class="carousel-btn" :disabled="lu.carouselIdx >= lu.images.length - 1" @click="lu.carouselIdx++">&rsaquo;</button>
      <span class="muted carousel-counter">{{ lu.carouselIdx + 1 }} / {{ lu.images.length }}</span>
    </div>

    <div v-if="COMMENTS_ENABLED && lu.showComments" style="margin-top:10px;border-top:1px solid var(--bd);padding-top:8px">
      <div v-for="c in topComments(lu)" :key="c.id" style="padding:6px 0">
        <div class="row"><strong>학부모</strong><span>{{ c.content }}</span>
          <span class="spacer"></span>
          <button v-if="!replyOf(lu, c)" class="primary" @click="reply(lu, c)">답글</button>
        </div>
        <div v-if="replyOf(lu, c)" class="muted" style="margin-left:16px">↳ 답글: {{ replyOf(lu, c).content }}</div>
      </div>
      <div v-if="!topComments(lu).length" class="muted">댓글 없음</div>
    </div>
  </div>
  <ImageLightbox :images="lbImages" :start-index="lbStart" :visible="lbVisible" @close="lbVisible = false" />
</template>

<style scoped>
.carousel {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  position: relative;
}
.carousel-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--bd);
  background: #fff;
  font-size: 20px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.carousel-btn:disabled {
  opacity: 0.3;
  cursor: default;
}
.carousel-img {
  max-width: 480px;
  max-height: 360px;
  border-radius: 6px;
  border: 1px solid var(--bd);
  object-fit: contain;
  cursor: pointer;
}
.carousel-counter {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 13px;
}
</style>
