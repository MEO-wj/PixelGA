import { ref, onUnmounted } from 'vue'

export interface GAMessage {
  type: 'init' | 'generation' | 'complete' | 'error'
  generation?: number
  similarity?: number
  mse?: number
  height?: number
  width?: number
  pixels?: number[][][]
  targetPixels?: number[][][]
  message?: string
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const lastMessage = ref<GAMessage | null>(null)
  const status = ref<'idle' | 'connecting' | 'running' | 'paused' | 'completed' | 'error'>('idle')
  const error = ref<string | null>(null)
  let currentTargetId = ''
  let reconnectAttempts = 0

  function connect(targetId: string) {
    if (ws.value) { ws.value.close(); ws.value = null }
    currentTargetId = targetId
    reconnectAttempts = 0
    error.value = null
    _doConnect()
  }

  function _doConnect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/evolve/${currentTargetId}`
    ws.value = new WebSocket(url)
    status.value = 'connecting'

    ws.value.onopen = () => {
      connected.value = true
      status.value = 'idle'
    }

    ws.value.onmessage = (event) => {
      const data: GAMessage = JSON.parse(event.data)
      lastMessage.value = data

      if (data.type === 'error') {
        error.value = data.message || '未知错误'
        status.value = 'error'
      } else if (data.type === 'init') {
        // 初始状态
      } else if (data.type === 'generation') {
        if (status.value !== 'paused') status.value = 'running'
      } else if (data.type === 'complete') {
        status.value = 'completed'
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      // 自动重连（最多 3 次）
      if (status.value !== 'idle' && reconnectAttempts < 3) {
        reconnectAttempts++
        setTimeout(_doConnect, 1000)
      }
    }

    ws.value.onerror = () => {
      connected.value = false
    }
  }

  function send(data: Record<string, unknown>) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      error.value = 'WebSocket 未连接，请重新上传图片'
      status.value = 'error'
    }
  }

  function start(params?: Record<string, unknown>) {
    send({ type: 'start', params })
  }

  function pause() {
    send({ type: 'pause' })
    status.value = 'paused'
  }

  function resume() {
    send({ type: 'resume' })
    status.value = 'running'
  }

  function reset() {
    send({ type: 'reset' })
    status.value = 'idle'
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
    status.value = 'idle'
    lastMessage.value = null
    error.value = null
  }

  onUnmounted(() => disconnect())

  return {
    connected,
    lastMessage,
    status,
    error,
    connect,
    disconnect,
    start,
    pause,
    resume,
    reset,
  }
}
