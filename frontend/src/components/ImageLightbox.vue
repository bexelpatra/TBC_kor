<script setup>
import { ref, watch, nextTick } from "vue";

const props = defineProps({
  images: { type: Array, required: true },
  startIndex: { type: Number, default: 0 },
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const overlay = ref(null);
const idx = ref(props.startIndex);
watch(() => props.startIndex, (v) => { idx.value = v; });
watch(() => props.visible, (v) => {
  if (v) {
    idx.value = props.startIndex;
    nextTick(() => overlay.value?.focus());
  }
});

function prev() { if (idx.value > 0) idx.value--; }
function next() { if (idx.value < props.images.length - 1) idx.value++; }

function onKey(e) {
  if (e.key === "Escape") emit("close");
  else if (e.key === "ArrowLeft") prev();
  else if (e.key === "ArrowRight") next();
}

function onBackdrop(e) {
  if (e.target === e.currentTarget) emit("close");
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="lb-overlay" @click="onBackdrop" @keydown="onKey" tabindex="0" ref="overlay">
      <button class="lb-close" @click="emit('close')">&times;</button>
      <button class="lb-arrow lb-prev" :disabled="idx === 0" @click="prev">&lsaquo;</button>
      <img :src="images[idx]" class="lb-img" />
      <button class="lb-arrow lb-next" :disabled="idx >= images.length - 1" @click="next">&rsaquo;</button>
      <span class="lb-counter">{{ idx + 1 }} / {{ images.length }}</span>
    </div>
  </Teleport>
</template>

<style scoped>
.lb-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
}
.lb-close {
  position: absolute;
  top: 16px;
  right: 24px;
  background: none;
  border: none;
  color: #fff;
  font-size: 36px;
  cursor: pointer;
  line-height: 1;
}
.lb-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: #fff;
  font-size: 48px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lb-arrow:disabled {
  opacity: 0.2;
  cursor: default;
}
.lb-prev { left: 24px; }
.lb-next { right: 24px; }
.lb-img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 4px;
}
.lb-counter {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 15px;
}
</style>
