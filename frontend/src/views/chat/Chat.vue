<!-- AI 对话页面 — SSE 流式输出 -->
<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useSSE } from '../../composables/useSSE'

const { isStreaming, start, abort } = useSSE()

/** 对话消息列表 */
const messages = ref([])
/** 输入框内容 */
const inputText = ref('')
/** 消息容器 DOM 引用 */
const chatContainer = ref(null)

/** 发送消息 */
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  await scrollToBottom()

  // 构建 API 请求的消息列表
  const apiMessages = messages.value.map(m => ({ role: m.role, content: m.content }))

  // 添加助手占位消息
  const assistantMsg = { role: 'assistant', content: '', isStreaming: true }
  messages.value.push(assistantMsg)

  await start('/api/agent/chat', { messages: apiMessages }, {
    onThinking(chunk) {
      assistantMsg.content += chunk
      scrollToBottom()
    },
    onDone() {
      assistantMsg.isStreaming = false
    },
    onError(msg) {
      assistantMsg.content = `[错误] ${msg}`
      assistantMsg.isStreaming = false
    },
  })
}

/** 停止生成 */
function stopGeneration() {
  abort()
}

/** 滚动到底部 */
async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

/** 清空对话 */
function clearChat() {
  messages.value = []
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <h2>AI 对话</h2>
      <el-button @click="clearChat" :disabled="isStreaming">清空对话</el-button>
    </div>

    <div ref="chatContainer" class="chat-messages">
      <div v-if="messages.length === 0" class="empty-hint">开始一段对话吧</div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="role-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
        <div class="content" v-text="msg.content" />
        <span v-if="msg.isStreaming" class="cursor">|</span>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入消息..."
        :disabled="isStreaming"
        @keydown.enter.exact.prevent="sendMessage"
      />
      <div class="input-actions">
        <el-button v-if="isStreaming" type="danger" @click="stopGeneration">停止</el-button>
        <el-button v-else type="primary" @click="sendMessage" :disabled="!inputText.trim()">发送</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.empty-hint { text-align: center; color: #999; margin-top: 40px; }
.message { margin-bottom: 16px; }
.message .role-label { font-weight: bold; margin-bottom: 4px; font-size: 13px; color: #666; }
.message.user .content { background: #ecf5ff; padding: 12px; border-radius: 8px; }
.message.assistant .content { background: #fff; padding: 12px; border-radius: 8px; border: 1px solid #e4e7ed; }
.cursor { animation: blink 1s infinite; color: #409eff; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
.chat-input { margin-top: 16px; }
.input-actions { display: flex; justify-content: flex-end; margin-top: 8px; gap: 8px; }
</style>
