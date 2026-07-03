/** SSE 流式请求封装 — 用于大模型对话和标注 */
import { ref } from 'vue'

/**
 * 发起 SSE POST 请求，返回流式控制器
 * @param {string} url - 请求路径
 * @param {object} body - 请求体
 * @param {object} callbacks - { onThinking, onDone, onError }
 * @returns {{ abort: Function }}
 */
export function useSSE() {
  const isStreaming = ref(false)
  let controller = null

  async function start(url, body, callbacks = {}) {
    const { onThinking, onDone, onError } = callbacks

    controller = new AbortController()
    isStreaming.value = true

    const token = localStorage.getItem('access_token')
    // 直连后端避免 Vite/Nginx 代理缓冲 SSE 流
    const apiPath = url.startsWith('/api') ? url : `/api${url}`
    const fullUrl = import.meta.env.DEV
      ? `http://localhost:8000${apiPath}`
      : apiPath

    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'thinking') {
                onThinking?.(event.content)
                // 让浏览器有机会渲染（避免一次性蹦出来）
                await new Promise(r => setTimeout(r, 0))
              }
              else if (event.type === 'done') onDone?.()
              else if (event.type === 'error') onError?.(event.content)
            } catch { /* 解析失败跳过 */ }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        onError?.(err.message)
      }
    } finally {
      isStreaming.value = false
    }
  }

  function abort() {
    controller?.abort()
    isStreaming.value = false
  }

  return { isStreaming, start, abort }
}
