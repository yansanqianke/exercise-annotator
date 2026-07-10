<!-- 首页 — 系统介绍 + 统计概览 -->
<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getSubjectsApi } from '../api/subject'
import { getKPsApi } from '../api/kp'
import { getQuestionsApi } from '../api/question'
import { EditPen, Refresh, Search } from '@element-plus/icons-vue'

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
    <!-- 系统介绍 -->
    <div class="hero">
      <h1 class="hero-title">习题知识点标注智能体</h1>
      <p class="hero-subtitle">
        基于 RAG + LLM 的自动化标注系统，帮助教师快速建立习题与知识点之间的关联
      </p>
    </div>

    <!-- 核心能力 -->
    <div class="features">
      <div class="feature-card">
        <div class="feature-icon"><el-icon :size="28"><EditPen /></el-icon></div>
        <h3>智能标注</h3>
        <p>输入题目即可自动识别涉及的知识点、难度等级和题型。支持选择题、判断题、简答题和编程题四种题型。</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon"><el-icon :size="28"><Refresh /></el-icon></div>
        <h3>双向驱动</h3>
        <p>教师手动创建知识点 + LLM 分析建议新知识点，教师确认后自动入库。知识库从零开始也能自然生长，解决冷启动问题。</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon"><el-icon :size="28"><Search /></el-icon></div>
        <h3>语义检索</h3>
        <p>知识点向量化存储，标注时自动检索相关候选。参考资料索引后在标注中提供上下文，提升标注准确度。</p>
      </div>
    </div>

    <!-- 工作流程 -->
    <div class="workflow">
      <h3>使用流程</h3>
      <div class="flow-steps">
        <div class="step"><span class="step-num">1</span>创建学科与知识点</div>
        <div class="step-arrow">→</div>
        <div class="step"><span class="step-num">2</span>导入题目（手动 / 文档）</div>
        <div class="step-arrow">→</div>
        <div class="step"><span class="step-num">3</span>点击标注，LLM 自动解析</div>
        <div class="step-arrow">→</div>
        <div class="step"><span class="step-num">4</span>确认结果或手动修正</div>
      </div>
    </div>

    <!-- 欢迎 + 统计 -->
    <div class="welcome-row">
      <span>欢迎回来，<strong>{{ authStore.user?.username }}</strong></span>
    </div>
    <div class="stats-grid">
      <div v-for="c in cards" :key="c.key" class="stat-card">
        <div class="stat-num" :style="{ color: c.color }">{{ stats[c.key] }}</div>
        <div class="stat-label">{{ c.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { padding: var(--space-2xl); max-width: 900px; }

/* 标题 */
.hero { margin-bottom: var(--space-xl); }
.hero-title { font-size: 32px; margin-bottom: 8px; }
.hero-subtitle { font-size: 16px; color: var(--color-text-secondary); line-height: 1.6; }

/* 核心能力 */
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-md); margin-bottom: var(--space-2xl); }
.feature-card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-lg);
}
.feature-icon { margin-bottom: 8px; color: var(--color-primary); }
.feature-card h3 { font-family: var(--font-heading); font-size: 16px; margin-bottom: 6px; }
.feature-card p { font-size: 13px; line-height: 1.6; color: var(--color-text-secondary); }

/* 工作流 */
.workflow { margin-bottom: var(--space-2xl); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: var(--space-lg); }
.workflow h3 { font-family: var(--font-heading); font-size: 16px; margin-bottom: 12px; }
.flow-steps { display: flex; align-items: center; gap: 12px; }
.step { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.step-num { width: 24px; height: 24px; border-radius: 50%; background: var(--color-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0; }
.step-arrow { color: var(--color-text-muted); font-size: 16px; }

/* 欢迎 + 统计 */
.welcome-row { margin-bottom: var(--space-md); font-size: 16px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-md); }
.stat-card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-lg); text-align: center;
}
.stat-num { font-size: 40px; font-weight: 700; font-family: var(--font-heading); line-height: 1.1; }
.stat-label { font-size: 13px; color: var(--color-text-muted); margin-top: 4px; }
</style>
