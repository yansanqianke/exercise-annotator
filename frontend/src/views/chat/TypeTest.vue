<!-- 打字机效果测试页 -->
<script setup>
import { ref, nextTick } from 'vue'

const text = ref('')
const running = ref(false)
let timer = null

async function start() {
  running.value = true
  const chars = '0123456789'.repeat(3) // "012345678901234567890123456789"
  text.value = ''
  for (let i = 0; i < chars.length; i++) {
    text.value += chars[i]
    await new Promise(r => setTimeout(r, 100))
    await nextTick()
  }
  running.value = false
}

function stop() {
  if (timer) clearInterval(timer)
  running.value = false
}
</script>

<template>
  <div style="padding:40px;max-width:600px;margin:0 auto">
    <h2>打字机效果测试</h2>
    <p>{{ text }}</p>
    <button @click="start" :disabled="running" style="padding:8px 16px;margin-right:8px">
      {{ running ? '运行中...' : '开始' }}
    </button>
    <button @click="stop" :disabled="!running" style="padding:8px 16px">停止</button>
  </div>
</template>
