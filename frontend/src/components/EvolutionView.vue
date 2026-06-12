<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{
  pixels: number[][][] | null
  targetPixels?: number[][][] | null
  height?: number
  width?: number
  pixelScale?: number
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const targetCanvasRef = ref<HTMLCanvasElement | null>(null)
const SCALE = props.pixelScale || 5

function drawCanvas(canvas: HTMLCanvasElement | null, data: number[][][] | null | undefined) {
  if (!canvas || !data) return
  const h = props.height || data.length
  const w = props.width || (data[0]?.length || h)
  canvas.width = w * SCALE
  canvas.height = h * SCALE
  const ctx = canvas.getContext('2d')!
  ctx.imageSmoothingEnabled = false
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const [r, g, b] = data[y]?.[x] ?? [0, 0, 0]
      ctx.fillStyle = `rgb(${r},${g},${b})`
      ctx.fillRect(x * SCALE, y * SCALE, SCALE, SCALE)
    }
  }
}

function draw() {
  drawCanvas(canvasRef.value, props.pixels)
  drawCanvas(targetCanvasRef.value, props.targetPixels)
}

watch(() => [props.pixels, props.targetPixels], draw, { deep: true })
onMounted(draw)

watch(() => props.pixels, draw, { deep: true })
onMounted(draw)
</script>

<template>
  <div class="evolution-view">
    <div class="canvas-row">
      <div class="canvas-col">
        <h4>🎯 目标图 (压缩后)</h4>
        <div class="canvas-wrapper">
          <canvas ref="targetCanvasRef" />
        </div>
        <p v-if="!targetPixels" class="placeholder">上传图片后显示</p>
      </div>
      <div class="canvas-col">
        <h4>🎨 进化结果</h4>
        <div class="canvas-wrapper">
          <canvas ref="canvasRef" />
        </div>
        <p v-if="!pixels" class="placeholder">上传图片后显示</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evolution-view {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.canvas-row {
  display: flex; gap: 16px; justify-content: center;
}
.canvas-col {
  flex: 1; text-align: center;
}
.canvas-col h4 { margin: 0 0 8px; font-size: 0.9rem; color: #555; }
.canvas-wrapper {
  display: flex; justify-content: center;
  background: #f0f0f0; border-radius: 8px; padding: 8px;
  min-height: 60px;
}
canvas { image-rendering: pixelated; max-width: 100%; }
.placeholder { color: #aaa; text-align: center; margin: 20px 0; font-size: 0.85rem; }
</style>
