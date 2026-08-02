<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, fileUrl } from "../../api/client";
import { fmtDateTime } from "../../util";

const route = useRoute();
const router = useRouter();
const n = ref(null);
const err = ref("");

onMounted(async () => {
  try { n.value = await api.get(`/api/notices/${route.params.id}`); }
  catch (e) { err.value = e.message; }
});
</script>

<template>
  <button @click="router.back()">‹ 목록</button>
  <p v-if="err" class="err">{{ err }}</p>
  <div v-if="n" class="card" style="margin-top:12px">
    <div class="row"><span class="tag">{{ n.serial_no }}</span><span class="muted">{{ fmtDateTime(n.notice_at) }}</span></div>
    <h2 style="margin:8px 0">{{ n.title }}</h2>
    <p style="white-space:pre-wrap">{{ n.content }}</p>
    <div v-for="img in n.images" :key="img.id"><img :src="fileUrl(img.url)" class="thumb" /></div>
  </div>
</template>
