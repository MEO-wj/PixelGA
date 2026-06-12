<script setup lang="ts">
import { ref, computed } from 'vue'
import ImageUploader from './components/ImageUploader.vue'
import EvolutionView from './components/EvolutionView.vue'
import ControlPanel from './components/ControlPanel.vue'
import StatsBar from './components/StatsBar.vue'
import { useWebSocket } from './composables/useWebSocket'

const { connected, lastMessage, status, error, connect, disconnect, start, pause, resume, reset: wsReset } = useWebSocket()

const targetId = ref<string | null>(null)
const generation = ref(0)
const similarity = ref(0)
const pixels = ref<number[][][] | null>(null)
const targetPixels = ref<number[][][] | null>(null)
const imgHeight = ref(64)
const imgWidth = ref(64)
const maxGenerations = ref(5000)
const pixelSize = ref(64)

function onUploaded(id: string) {
  targetId.value = id
  disconnect()
  connect(id)
}

function onStart(params: Record<string, unknown>) {
  if (!targetId.value) return
  maxGenerations.value = params.maxGenerations as number
  pixelSize.value = params.pixelSize as number
  start(params)
}

function onReset() {
  wsReset()
  generation.value = 0
  similarity.value = 0
  pixels.value = null
}

function onDownload() {
  if (!targetId.value) return
  window.open(`/api/download/${targetId.value}`, '_blank')
}

// 监听 WebSocket 消息
import { watch } from 'vue'
watch(lastMessage, (msg) => {
  if (!msg) return
  if (msg.type === 'init' || msg.type === 'generation') {
    generation.value = msg.generation ?? 0
    similarity.value = msg.similarity ?? 0
    if (msg.height) imgHeight.value = msg.height
    if (msg.width) imgWidth.value = msg.width
    if (msg.pixels) pixels.value = msg.pixels
    if (msg.targetPixels) targetPixels.value = msg.targetPixels
  } else if (msg.type === 'complete') {
    generation.value = msg.generation ?? generation.value
  }
})

const hasTarget = computed(() => targetId.value !== null)
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>🎨 像素画进化系统</h1>
      <p class="subtitle">基于遗传算法的图像逼近</p>
    </header>

    <div class="main-layout">
      <aside class="left-panel">
        <ImageUploader :pixel-size="pixelSize" @uploaded="onUploaded" />
        <ControlPanel
          :status="status"
          :has-target="hasTarget"
          v-model:pixel-size="pixelSize"
          @start="onStart"
          @pause="pause"
          @resume="resume"
          @reset="onReset"
          @download="onDownload"
        />
      </aside>

      <main class="center-panel">
        <div v-if="error" class="error-banner">⚠ {{ error }}</div>
        <StatsBar
          :generation="generation"
          :similarity="similarity"
          :max-generations="maxGenerations"
          :status="status"
        />
        <EvolutionView :pixels="pixels" :target-pixels="targetPixels" :height="imgHeight" :width="imgWidth" :pixel-scale="pixelSize <= 64 ? 5 : pixelSize <= 128 ? 3 : 2" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}
.app-header {
  text-align: center;
  margin-bottom: 24px;
}
.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
  color: #333;
}
.subtitle {
  margin: 4px 0 0;
  color: #888;
  font-size: 0.95rem;
}
.main-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  align-items: start;
}
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.center-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.error-banner {
  background: #ffe0e0; color: #c0392b; padding: 10px 16px;
  border-radius: 8px; font-size: 0.9rem;
}

@media (max-width: 768px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}
</style>
