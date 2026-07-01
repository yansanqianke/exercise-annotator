<!-- 首页 Dashboard -->
<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { getSubjectsApi } from '../api/subject'
import { getKPsApi } from '../api/kp'
import { getQuestionsApi } from '../api/question'

const authStore = useAuthStore()
const router = useRouter()

/** 统计数据 */
const stats = ref({ subjects: 0, kps: 0, questions: 0 })

async function loadStats() {
  try {
    const [subjects, kps, questions] = await Promise.all([
      getSubjectsApi(),
      getKPsApi(),
      getQuestionsApi({}),
    ])
    stats.value = {
      subjects: subjects.length,
      kps: kps.length,
      questions: questions.length,
    }
  } catch { /* */ }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(loadStats)
</script>

<template>
  <div class="dashboard">
    <div class="header">
      <h1>习题知识点标注智能体</h1>
      <div>
        <span style="margin-right: 16px">
          {{ authStore.user?.username }}（{{ authStore.user?.role === 'admin' ? '管理员' : '教师' }}）
        </span>
        <el-button type="danger" size="small" @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card"><div class="stat-num">{{ stats.subjects }}</div><div class="stat-label">学科数</div></el-card>
      <el-card class="stat-card"><div class="stat-num">{{ stats.kps }}</div><div class="stat-label">知识点</div></el-card>
      <el-card class="stat-card"><div class="stat-num">{{ stats.questions }}</div><div class="stat-label">已标注题目</div></el-card>
    </div>

    <h3>功能导航</h3>
    <div class="nav-cards">
      <el-card><router-link to="/subjects">学科管理</router-link></el-card>
      <el-card><router-link to="/knowledge-points">知识点管理</router-link></el-card>
      <el-card><router-link to="/annotate">题目标注</router-link></el-card>
      <el-card><router-link to="/documents">文档管理</router-link></el-card>
      <el-card><router-link to="/chat">AI 对话</router-link></el-card>
    </div>

    <template v-if="authStore.isAdmin">
      <h3 style="margin-top: 24px">系统管理</h3>
      <div class="nav-cards">
        <el-card><router-link to="/admin/users">用户管理</router-link></el-card>
        <el-card><router-link to="/admin/llm-config">大模型配置</router-link></el-card>
        <el-card><router-link to="/admin/agents">智能体管理</router-link></el-card>
        <el-card><router-link to="/admin/logs">系统日志</router-link></el-card>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.stats-row { display: flex; gap: 16px; margin-bottom: 24px; }
.stat-card { flex: 1; text-align: center; }
.stat-num { font-size: 32px; font-weight: bold; color: #409eff; }
.stat-label { font-size: 14px; color: #999; margin-top: 4px; }
.nav-cards { display: flex; gap: 16px; flex-wrap: wrap; }
.nav-cards .el-card { width: 200px; text-align: center; font-size: 16px; }
</style>
