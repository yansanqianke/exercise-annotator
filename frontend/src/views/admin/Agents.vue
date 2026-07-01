<!-- 智能体管理页面 -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAgentsApi, createAgentApi, updateAgentApi } from '../../api/admin'

const agents = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const form = ref({ id: null, name: '', description: '', agent_type: 'annotator', config_json: '{}', is_active: true })

async function load() { agents.value = await getAgentsApi() }

function openCreate() {
  isEditing.value = false
  form.value = { id: null, name: '', description: '', agent_type: 'annotator', config_json: '{}', is_active: true }
  dialogVisible.value = true
}
function openEdit(row) {
  isEditing.value = true
  form.value = { ...row }
  dialogVisible.value = true
}
async function handleSubmit() {
  if (isEditing.value) {
    await updateAgentApi(form.value.id, {
      name: form.value.name, description: form.value.description,
      config_json: form.value.config_json, is_active: form.value.is_active,
    })
  } else {
    await createAgentApi(form.value)
  }
  ElMessage.success(isEditing.value ? '已更新' : '已创建')
  dialogVisible.value = false
  load()
}
onMounted(load)
</script>

<template>
  <div class="page">
    <div class="header"><h2>智能体管理</h2><el-button type="primary" @click="openCreate">创建智能体</el-button></div>
    <el-table :data="agents" border>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="agent_type" label="类型" width="100" />
      <el-table-column label="启用" width="70">
        <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }"><el-button size="small" @click="openEdit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑智能体' : '创建智能体'" width="500px">
      <el-form @submit.prevent="handleSubmit">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.agent_type" style="width:100%">
            <el-option label="标注智能体" value="annotator" />
            <el-option label="对话智能体" value="chat" />
          </el-select>
        </el-form-item>
        <el-form-item label="配置 JSON"><el-input v-model="form.config_json" type="textarea" :rows="3" placeholder='{"top_k":5}' /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="handleSubmit">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
