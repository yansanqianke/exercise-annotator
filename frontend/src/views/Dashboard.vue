<!-- 首页 Dashboard（占位） -->
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
    <h1>习题知识点标注智能体</h1>
    <p>欢迎，{{ authStore.user?.username }}（{{ authStore.user?.role === 'admin' ? '管理员' : '教师' }}）</p>
    <el-button type="danger" @click="handleLogout">退出登录</el-button>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 40px;
  text-align: center;
}
</style>
