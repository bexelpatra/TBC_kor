<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../../api/client";
import { fmtDateTime, toISO } from "../../util";
import Pager from "../../components/Pager.vue";

const router = useRouter();
const items = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const title = ref("");
const dateFrom = ref("");
const dateTo = ref("");
const err = ref("");

async function load() {
  err.value = "";
  const q = new URLSearchParams({ page: page.value, size: size.value });
  if (title.value) q.set("title", title.value);
  if (dateFrom.value) q.set("date_from", toISO(dateFrom.value));
  if (dateTo.value) q.set("date_to", toISO(dateTo.value));
  try {
    const d = await api.get(`/api/lectures?${q}`);
    items.value = d.items;
    total.value = d.total;
  } catch (e) { err.value = e.message; }
}
function search() { page.value = 1; load(); }
function setPage(p) { page.value = p; load(); }
function setSize(s) { size.value = s; page.value = 1; load(); }

onMounted(load);
</script>

<template>
  <h2>특강 내역</h2>
  <div class="card">
    <div class="row">
      <input type="date" v-model="dateFrom" /> ~ <input type="date" v-model="dateTo" />
      <input v-model="title" placeholder="제목 검색" @keyup.enter="search" />
      <button class="primary" @click="search">검색</button>
    </div>
  </div>

  <p v-if="err" class="err">{{ err }}</p>
  <table style="margin-top:14px">
    <thead><tr><th style="width:60px">회차</th><th>제목</th><th style="width:170px">일시</th></tr></thead>
    <tbody>
      <tr v-for="it in items" :key="it.id" class="clickable" @click="router.push(`/lectures/${it.id}`)">
        <td>{{ it.round_no }}</td>
        <td>{{ it.title }}</td>
        <td>{{ fmtDateTime(it.lecture_at) }}</td>
      </tr>
      <tr v-if="!items.length"><td colspan="3" class="muted">특강 내역이 없습니다.</td></tr>
    </tbody>
  </table>
  <Pager :total="total" :page="page" :size="size" @update:page="setPage" @update:size="setSize" />
</template>
