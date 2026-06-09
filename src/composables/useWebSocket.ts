/**
 * useWebSocket - WebSocket 实时进度推送
 *
 * 替代轮询机制，通过 WebSocket 接收任务进度实时更新
 *
 * 使用示例：
 * const { connect, disconnect, progress, status, isConnected } = useWebSocket()
 * connect(jobId)  // 连接到任务
 * // 监听 progress 和 status 变化
 */
import { ref, computed, onUnmounted } from 'vue'

export interface TaskProgress {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  error?: string
  timestamp?: number
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const progress = ref(0)
  const status = ref<'idle' | 'pending' | 'processing' | 'completed' | 'failed'>('idle')
  const message = ref('')
  const error = ref('')
  const jobId = ref('')

  // 心跳定时器
  let heartbeatInterval: NodeJS.Timeout | null = null

  /**
   * 连接到 WebSocket
   * @param taskJobId 任务ID
   */
  const connect = (taskJobId: string) => {
    jobId.value = taskJobId
    progress.value = 0
    status.value = 'pending'
    message.value = ''
    error.value = ''

    // 获取 token
    const token = localStorage.getItem('access_token')
    const envWsUrl = import.meta.env.VITE_WS_URL
    const wsBaseUrl = envWsUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
    const url = `${wsBaseUrl}/api/v1/ws/jobs/${taskJobId}${token ? `?token=${token}` : ''}`

    try {
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        console.log(`WebSocket connected to job ${taskJobId}`)
        isConnected.value = true

        // 启动心跳
        startHeartbeat()
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.value.onerror = (event) => {
        console.error('WebSocket error:', event)
        error.value = 'WebSocket connection error'
        isConnected.value = false
      }

      ws.value.onclose = (event) => {
        console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`)
        isConnected.value = false
        stopHeartbeat()

        // 如果不是正常关闭，尝试重连（可选）
        if (event.code !== 1000 && event.code !== 1001) {
          console.log('Attempting to reconnect in 3s...')
          setTimeout(() => {
            if (status.value !== 'completed' && status.value !== 'failed') {
              connect(taskJobId)
            }
          }, 3000)
        }
      }
    } catch (e) {
      console.error('Failed to create WebSocket:', e)
      error.value = 'Failed to connect to WebSocket'
    }
  }

  /**
   * 处理接收到的消息
   */
  const handleMessage = (data: any) => {
    switch (data.type) {
      case 'progress':
        progress.value = data.progress || 0
        status.value = data.status || 'processing'
        message.value = data.message || ''
        break

      case 'complete':
        progress.value = 100
        status.value = 'completed'
        message.value = data.message || 'Task completed'
        // 任务完成后自动断开
        setTimeout(() => disconnect(), 1000)
        break

      case 'error':
        status.value = 'failed'
        error.value = data.error || 'Task failed'
        // 失败后自动断开
        setTimeout(() => disconnect(), 1000)
        break

      default:
        console.log('Unknown message type:', data.type)
    }
  }

  /**
   * 启动心跳机制
   */
  const startHeartbeat = () => {
    heartbeatInterval = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send('ping')
      }
    }, 30000) // 每30秒发送一次心跳
  }

  /**
   * 停止心跳
   */
  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
  }

  /**
   * 断开 WebSocket 连接
   */
  const disconnect = () => {
    stopHeartbeat()

    if (ws.value) {
      ws.value.close(1000, 'Client disconnect')
      ws.value = null
    }

    isConnected.value = false
  }

  /**
   * 发送消息（一般用于心跳或自定义消息）
   */
  const send = (data: string | object) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  /**
   * 计算属性：是否正在处理
   */
  const isProcessing = computed(() => {
    return status.value === 'pending' || status.value === 'processing'
  })

  /**
   * 计算属性：是否完成
   */
  const isCompleted = computed(() => {
    return status.value === 'completed'
  })

  /**
   * 计算属性：是否失败
   */
  const isFailed = computed(() => {
    return status.value === 'failed'
  })

  // 组件卸载时自动断开
  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    isConnected,
    progress,
    status,
    message,
    error,
    jobId,

    // Computed
    isProcessing,
    isCompleted,
    isFailed,

    // Methods
    connect,
    disconnect,
    send,
  }
}
