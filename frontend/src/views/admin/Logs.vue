<!-- 系统日志页面 -->
<script setup>
import { ref, onMounted } from 'vue'
import { getLogsApi } from '../../api/admin'

const logs = ref([])
const filter = ref({ action: '' })

async function load() {
  const params = {}
  if (filter.value.action) params.action = filter.value.action
  logs.value = await getLogsApi(params)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="header">
      
      <el-select v-model="filter.action" placeholder="按动作过滤" clearable @change="load" style="width:180px">
        <el-option label="标注" value="annotate" />
        <el-option label="对话" value="chat" />
      </el-select>
    </div>
    <el-table :data="logs" border max-height="600">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="user_id" label="用户ID" width="70" />
      <el-table-column prop="action" label="动作" width="100" />
      <el-table-column prop="input_summary" label="输入摘要" show-overflow-tooltip />
      <el-table-column prop="tokens_used" label="Token" width="80" />
      <el-table-column prop="latency_ms" label="耗时ms" width="90" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }"><el-tag :type="row.status==='success'?'success':'danger'" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160" />
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
