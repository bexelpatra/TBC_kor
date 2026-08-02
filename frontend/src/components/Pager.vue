<script setup>
// 페이징 + 페이지 크기(10/20/30) 셀렉트.
const props = defineProps({ total: Number, page: Number, size: Number });
const emit = defineEmits(["update:page", "update:size"]);

function lastPage() {
  return Math.max(1, Math.ceil((props.total || 0) / (props.size || 10)));
}
</script>

<template>
  <div class="row" style="margin-top: 12px">
    <button :disabled="page <= 1" @click="emit('update:page', page - 1)">‹ 이전</button>
    <span class="muted">{{ page }} / {{ lastPage() }} (총 {{ total }}건)</span>
    <button :disabled="page >= lastPage()" @click="emit('update:page', page + 1)">다음 ›</button>
    <span class="spacer"></span>
    <select :value="size" @change="emit('update:size', Number($event.target.value))">
      <option :value="10">10개</option>
      <option :value="20">20개</option>
      <option :value="30">30개</option>
    </select>
  </div>
</template>
