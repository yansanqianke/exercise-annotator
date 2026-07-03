<!-- AI 对话 — 流式气泡界面 -->
<script setup>
import { ref, nextTick, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const isStreaming = ref(false)
const messages = ref([])
const inputText = ref('')
const chatContainer = ref(null)
const inputRef = ref(null)
let abortController = null

// ===== 逐字动画引擎 =====
const textQueue = ref([])       // 待渲染的字符队列
let animatorTimer = null        // setInterval ID
let targetMsg = null            // 当前正在动画的 message 对象

/** 启动逐字动画 — 每 25ms 从队列取出 1-3 个字符追加到消息中 */
function startAnimator(msg) {
  targetMsg = msg
  if (animatorTimer) return  // 已在运行

  animatorTimer = setInterval(() => {
    if (textQueue.value.length === 0 && !isStreaming.value) {
      stopAnimator()
      return
    }
    // 每次取 1-3 个字符（英文多取，中文少取）
    const take = textQueue.value.length > 0
      ? Math.min(textQueue.value.length, 2)
      : 0
    if (take > 0) {
      const chars = textQueue.value.splice(0, take)
      targetMsg.content += chars.join('')
      scrollToBottom()
    }
  }, 25)
}

function stopAnimator() {
  if (animatorTimer) {
    clearInterval(animatorTimer)
    animatorTimer = null
  }
  // 清空剩余队列
  if (targetMsg && textQueue.value.length > 0) {
    targetMsg.content += textQueue.value.join('')
    textQueue.value = []
  }
  if (targetMsg) {
    targetMsg.isStreaming = false
    targetMsg = null
  }
  scrollToBottom()
}

onUnmounted(stopAnimator)

/** 将文本 chunk 拆分为字符数组推入队列 */
function enqueueText(text) {
  textQueue.value.push(...text.split(''))
}

// ===== 发送消息（直连后端，不经过代理） =====
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  const apiMessages = messages.value
    .filter(m => !m.isStreaming)
    .map(m => ({ role: m.role, content: m.content }))

  const assistantMsg = { role: 'assistant', content: '', isStreaming: true }
  messages.value.push(assistantMsg)
  startAnimator(assistantMsg)

  isStreaming.value = true
  const token = localStorage.getItem('access_token')
  abortController = new AbortController()

  try {
    const url = import.meta.env.DEV
      ? 'http://localhost:8000/api/agent/chat'
      : '/api/agent/chat'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ messages: apiMessages }),
      signal: abortController.signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'thinking') enqueueText(event.content)
          else if (event.type === 'error') throw new Error(event.content)
        } catch (e) {
          if (e.message && !e.message.startsWith('Unexpected')) throw e
        }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      stopAnimator()
      assistantMsg.content = e.message
    }
  } finally {
    isStreaming.value = false
  }
}

function stopGeneration() {
  abortController?.abort()
  stopAnimator()
  const last = messages.value[messages.value.length - 1]
  if (last && !last.content) last.content = '（已停止生成）'
}

function clearChat() {
  stopAnimator()
  messages.value = []
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(() => isStreaming.value, (v) => {
  if (!v) inputRef.value?.focus()
})
</script>

<template>
  <div class="chat-shell">
    <!-- 消息区 -->
    <div ref="chatContainer" class="chat-body">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-illustration">
          <span class="empty-icon">✦</span>
        </div>
        <h3>开始一段对话</h3>
        <p>向 AI 助教提问关于学科知识、题目解析等问题</p>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role]">
        <div class="msg-avatar">
          {{ msg.role === 'user' ? '👤' : '✦' }}
        </div>
        <div class="msg-body">
          <div class="msg-bubble" :class="{ streaming: msg.isStreaming }">
            <template v-if="msg.error">{{ msg.error }}</template>
            <template v-else>{{ msg.content || (msg.isStreaming ? '' : '…') }}</template>
            <span v-if="msg.isStreaming" class="typing-cursor">|</span>
          </div>
          <!-- 流式进行中提示 -->
          <div v-if="msg.isStreaming && !msg.content" class="streaming-hint">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-foot">
      <div class="input-row">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-textarea"
          placeholder="输入消息… (Enter 发送)"
          :disabled="isStreaming"
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @input="e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px' }"
        ></textarea>
        <button
          v-if="isStreaming"
          class="btn-send stop"
          @click="stopGeneration"
        >停止</button>
        <button
          v-else
          class="btn-send"
          :disabled="!inputText.trim()"
          @click="sendMessage"
        >发送</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 760px;
  margin: 0 auto;
}

/* ===== 消息区 ===== */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xl) var(--space-lg);
  scroll-behavior: smooth;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  text-align: center;
}
.empty-illustration {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5f0e8, #ebe4d8);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: var(--space-lg);
}
.empty-icon { font-size: 28px; color: var(--color-accent); }
.empty-state h3 {
  font-family: var(--font-heading); font-size: 20px;
  margin-bottom: 8px; color: var(--color-text);
}
.empty-state p { font-size: 14px; color: var(--color-text-muted); }

/* 消息行 */
.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: var(--space-lg);
  animation: msgIn .3s ease-out;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;
}
.msg-row.user .msg-avatar { background: #e8ecf6; }
.msg-row.assistant .msg-avatar { background: #faf0e0; }

.msg-body { max-width: 85%; min-width: 60px; }

/* 气泡 */
.msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14.5px;
  line-height: 1.7;
  word-break: break-word;
}
.msg-row.user .msg-bubble {
  background: #e8ecf6;
  color: var(--color-text);
  border-bottom-right-radius: 4px;
}
.msg-row.assistant .msg-bubble {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

/* 流式打字光标 */
.typing-cursor {
  color: var(--color-accent);
  animation: blink .8s infinite;
  font-weight: 300;
  margin-left: 1px;
}
@keyframes blink {
  0%, 50%  { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 加载提示 */
.streaming-hint {
  display: flex; gap: 4px; padding: 8px 16px;
}
.dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: .15s; }
.dot:nth-child(3) { animation-delay: .3s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: .4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ===== 输入区 ===== */
.chat-foot {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}
.chat-textarea {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 120px;
  background: var(--color-bg);
  transition: border-color .15s;
}
.chat-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(44,62,107,.08);
}
.chat-textarea:disabled {
  background: var(--color-surface);
  cursor: not-allowed;
}

.btn-send {
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  background: var(--color-primary);
  color: #fff;
  transition: all .15s;
  flex-shrink: 0;
  white-space: nowrap;
}
.btn-send:hover:not(:disabled) {
  background: var(--color-primary-light);
}
.btn-send:disabled {
  opacity: .4;
  cursor: not-allowed;
}
.btn-send.stop {
  background: var(--color-danger);
}
</style>
