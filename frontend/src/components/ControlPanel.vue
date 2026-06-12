<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  status: 'idle' | 'connecting' | 'running' | 'paused' | 'completed'
  hasTarget: boolean
  pixelSize: number
}>()

const emit = defineEmits<{
  start: [params: Record<string, unknown>]
  pause: []
  resume: []
  reset: []
  download: []
  'update:pixelSize': [value: number]
}>()

const popSize = ref(100)
const mutationRate = ref(0.05)
const maxGenerations = ref(5000)
const localPixelSize = computed({
  get: () => props.pixelSize,
  set: (v) => emit('update:pixelSize', v)
})

function onStart() {
  emit('start', {
    popSize: popSize.value,
    mutationRate: mutationRate.value,
    maxGenerations: maxGenerations.value,
    pixelSize: localPixelSize.value,
  })
}
</script>

<template>
  <div class="control-card">
    <h3>🎮 控制面板</h3>

    <div class="param-group">
      <label>种群大小 <span>{{ popSize }}</span></label>
      <input type="range" v-model.number="popSize" min="10" max="200" step="10" />

      <label>变异率 <span>{{ mutationRate }}</span></label>
      <input type="range" v-model.number="mutationRate" min="0.005" max="0.2" step="0.005" />

      <label>最大代数 <span>{{ maxGenerations }}</span></label>
      <input type="range" v-model.number="maxGenerations" min="100" max="10000" step="100" />

      <label>像素尺寸 <span>{{ localPixelSize }}px</span></label>
      <input type="range" v-model.number="localPixelSize" min="16" max="256" step="16" />
    </div>

    <div class="buttons">
      <button
        class="btn btn-primary"
        @click="onStart"
        :disabled="!hasTarget || status === 'running'"
      >▶ 开始进化</button>

      <button
        class="btn btn-warning"
        @click="emit('pause')"
        :disabled="status !== 'running'"
      >⏸ 暂停</button>

      <button
        class="btn btn-info"
        @click="emit('resume')"
        :disabled="status !== 'paused'"
      >▶ 继续</button>

      <button
        class="btn btn-danger"
        @click="emit('reset')"
        :disabled="status === 'idle' || status === 'connecting'"
      >↺ 重置</button>

      <button
        class="btn btn-success"
        @click="emit('download')"
        :disabled="status === 'idle' || status === 'connecting'"
      >⬇ 下载结果</button>
    </div>
  </div>
</template>

<style scoped>
.control-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.control-card h3 { margin: 0 0 12px; font-size: 1rem; }
.param-group label {
  display: flex; justify-content: space-between;
  font-size: 0.85rem; color: #555; margin-bottom: 2px;
}
.param-group label span { font-weight: 600; color: #6C5CE7; }
.param-group input[type="range"] {
  width: 100%; margin-bottom: 10px; accent-color: #6C5CE7;
}
.buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.btn {
  flex: 1; min-width: 60px; padding: 10px 8px; border: none; border-radius: 8px;
  font-size: 0.85rem; cursor: pointer; transition: opacity 0.2s; color: #fff;
}
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary { background: #6C5CE7; }
.btn-warning { background: #f39c12; }
.btn-info { background: #3498db; }
.btn-danger { background: #e74c3c; }
.btn-success { background: #27ae60; }
.btn:not(:disabled):hover { opacity: 0.85; }
</style>
