<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps<{
  pixelSize?: number
}>()

const emit = defineEmits<{
  uploaded: [targetId: string]
}>()

const uploading = ref(false)
const previewUrl = ref<string | null>(null)
const error = ref<string | null>(null)

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片文件'
    return
  }

  error.value = null
  uploading.value = true

  try {
    const form = new FormData()
    form.append('file', file)
    const res = await axios.post('/api/upload', form, {
      params: { pixelSize: props.pixelSize || 64 }
    })
    emit('uploaded', res.data.target_id)

    previewUrl.value = URL.createObjectURL(file)
  } catch {
    error.value = '上传失败，请检查后端是否启动'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="uploader-card">
    <h3>📷 上传目标图片</h3>
    <label class="upload-area" :class="{ uploading }">
      <input type="file" accept="image/*" @change="onFileChange" :disabled="uploading" />
      <span v-if="uploading">⏳ 上传中...</span>
      <span v-else>点击或拖拽上传图片</span>
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <img v-if="previewUrl" :src="previewUrl" class="preview" alt="目标图预览" />
  </div>
</template>

<style scoped>
.uploader-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.uploader-card h3 { margin: 0 0 12px; font-size: 1rem; }
.upload-area {
  display: flex; align-items: center; justify-content: center;
  height: 80px; border: 2px dashed #ccc; border-radius: 8px;
  cursor: pointer; transition: border-color 0.2s;
}
.upload-area:hover { border-color: #6C5CE7; }
.upload-area.uploading { opacity: 0.6; pointer-events: none; }
.upload-area input { display: none; }
.upload-area span { color: #888; font-size: 0.9rem; }
.error { color: #e74c3c; font-size: 0.85rem; margin: 8px 0 0; }
.preview { width: 100%; margin-top: 12px; border-radius: 8px; image-rendering: pixelated; }
</style>
