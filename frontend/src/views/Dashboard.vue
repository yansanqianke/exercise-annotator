<!-- 首页 — 统计概览 -->
<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getSubjectsApi } from '../api/subject'
import { getKPsApi } from '../api/kp'
import { getQuestionsApi } from '../api/question'

const authStore = useAuthStore()
const stats = ref({ subjects: 0, kps: 0, questions: 0, annotated: 0 })

async function loadStats() {
  try {
    const [subjects, kps, questions] = await Promise.all([
      getSubjectsApi(), getKPsApi(), getQuestionsApi({}),
    ])
    stats.value = {
      subjects: subjects.length, kps: kps.length,
      questions: questions.length,
      annotated: questions.filter(q => q.kp_maps?.length).length,
    }
  } catch { /* */ }
}

const cards = [
  { key: 'subjects', label: '学科', color: '#5a7d8c' },
  { key: 'kps', label: '知识点', color: '#c4872b' },
  { key: 'questions', label: '题库', color: '#2c3e6b' },
  { key: 'annotated', label: '已标注', color: '#5b8c5a' },
]

onMounted(loadStats)
</script>

<template>
  <div class="dashboard">
    <h1 class="welcome">
      欢迎回来，<span class="name">{{ authStore.user?.username }}</span>
    </h1>
    <p class="subtitle">习题知识点标注智能体</p>

    <div class="stats-grid">
      <div v-for="c in cards" :key="c.key" class="stat-card">
        <div class="stat-num" :style="{ color: c.color }">{{ stats[c.key] }}</div>
        <div class="stat-label">{{ c.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: var(--space-2xl);
  max-width: 800px;
}
.welcome { font-size: 28px; margin-bottom: 4px; }
.welcome .name { color: var(--color-accent); }
.subtitle { color: var(--color-text-muted); margin-bottom: var(--space-xl); font-size: 15px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
}
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  text-align: center;
  transition: box-shadow .2s;
}
.stat-card:hover { box-shadow: var(--shadow-md); }
.stat-num { font-size: 40px; font-weight: 700; font-family: var(--font-heading); line-height: 1.1; }
.stat-label { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }
</style>
