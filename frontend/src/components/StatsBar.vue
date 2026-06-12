<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  generation: number
  similarity: number
  maxGenerations: number
  status: string
}>()

const similarityText = computed(() => {
  return props.similarity.toFixed(1) + '%'
})

const progress = computed(() => {
  return Math.min(100, (props.generation / props.maxGenerations) * 100)
})

const statusText = computed(() => {
  switch (props.status) {
    case 'idle': return '就绪'
    case 'connecting': return '连接中...'
    case 'running': return '进化中...'
    case 'paused': return '已暂停'
    case 'completed': return '进化完成 ✓'
    default: return props.status
  }
})
</script>

<template>
  <div class="stats-bar">
    <div class="stat">
      <span class="label">状态</span>
      <span class="value status" :class="status">{{ statusText }}</span>
    </div>
    <div class="stat">
      <span class="label">代数</span>
      <span class="value">{{ generation }} / {{ maxGenerations }}</span>
    </div>
    <div class="stat">
      <span class="label">相似度</span>
      <span class="value">{{ similarityText }}</span>
    </div>
    <div class="progress-bar">
      <div class="fill" :style="{ width: progress + '%' }" />
    </div>
  </div>
</template>

<style scoped>
.stats-bar {
  background: #fff; border-radius: 12px; padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  display: flex; flex-wrap: wrap; gap: 16px; align-items: center;
}
.stat { display: flex; flex-direction: column; gap: 2px; }
.label { font-size: 0.8rem; color: #888; }
.value { font-size: 1.1rem; font-weight: 700; color: #333; }
.value.status { font-size: 0.95rem; }
.status.running { color: #6C5CE7; }
.status.paused { color: #f39c12; }
.status.completed { color: #27ae60; }
.progress-bar {
  flex: 1; min-width: 120px; height: 6px; background: #eee; border-radius: 3px;
}
.fill {
  height: 100%; background: linear-gradient(90deg, #6C5CE7, #a29bfe);
  border-radius: 3px; transition: width 0.3s;
}
</style>
