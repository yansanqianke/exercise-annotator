<!-- 用户管理页面（admin 专有） -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUsersApi, updateUserRoleApi, updateUserActiveApi } from '../../api/admin'

const users = ref([])

async function load() { users.value = await getUsersApi() }

async function changeRole(user, role) {
  await updateUserRoleApi(user.id, role)
  ElMessage.success('角色已更新')
  load()
}

async function toggleActive(user) {
  await updateUserActiveApi(user.id, !user.is_active)
  ElMessage.success(user.is_active ? '已禁用' : '已启用')
  load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h2>用户管理</h2>
    <el-table :data="users" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-select :model-value="row.role" @change="r => changeRole(row, r)" size="small">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button size="small" :type="row.is_active ? 'danger' : 'success'" @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 24px; }
</style>
