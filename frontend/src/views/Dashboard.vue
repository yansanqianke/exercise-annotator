<!-- 首页 Dashboard -->
<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

/** 退出登录 */
function handleLogout() {
  authStore.logout()
  router.push('/login')
}
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

    <div class="nav-cards">
      <el-card><router-link to="/subjects">学科管理</router-link></el-card>
      <el-card><router-link to="/knowledge-points">知识点管理</router-link></el-card>
      <el-card><router-link to="/chat">AI 对话</router-link></el-card>
      <el-card v-if="authStore.isAdmin"><router-link to="/admin/llm-config">大模型配置</router-link></el-card>
    </div>
  </div>
</template>

<style scoped>
.dashboard { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.nav-cards { display: flex; gap: 16px; }
.nav-cards .el-card { width: 200px; text-align: center; font-size: 16px; }
</style>
