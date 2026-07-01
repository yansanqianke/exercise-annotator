<!-- 大模型配置管理页面（admin 专有） -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getLLMConfigsApi, createLLMConfigApi,
  updateLLMConfigApi, activateLLMConfigApi, deleteLLMConfigApi,
} from '../../api/llm'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const form = ref({ id: null, name: '', provider: 'deepseek', model: '', api_key: '', base_url: '' })

async function loadConfigs() {
  loading.value = true
  try { configs.value = await getLLMConfigsApi() }
  catch { /* 拦截器已处理 */ }
  finally { loading.value = false }
}

function openCreate() {
  isEditing.value = false
  form.value = { id: null, name: '', provider: 'deepseek', model: '', api_key: '', base_url: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  isEditing.value = true
  form.value = { ...row, api_key: '' }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    const data = { ...form.value }
    if (isEditing.value && !data.api_key) delete data.api_key
    if (isEditing.value) {
      await updateLLMConfigApi(form.value.id, data)
      ElMessage.success('已更新')
    } else {
      await createLLMConfigApi(data)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await loadConfigs()
  } catch { /* 拦截器已处理 */ }
}

async function handleActivate(row) {
  await activateLLMConfigApi(row.id)
  ElMessage.success('已激活')
  await loadConfigs()
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除 "${row.name}"？`, '确认删除', { type: 'warning' })
    await deleteLLMConfigApi(row.id)
    ElMessage.success('已删除')
    await loadConfigs()
  } catch { /* 取消或失败 */ }
}

import { ElMessageBox } from 'element-plus'

onMounted(loadConfigs)
</script>

<template>
  <div class="llm-config">
    <div class="header">
      <h2>大模型配置</h2>
      <el-button type="primary" @click="openCreate">创建配置</el-button>
    </div>

    <el-table :data="configs" v-loading="loading" border>
      <el-table-column prop="name" label="配置名称" width="160" />
      <el-table-column prop="provider" label="提供商" width="100" />
      <el-table-column prop="model" label="模型" width="160" />
      <el-table-column prop="base_url" label="API 端点" show-overflow-tooltip />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_active" type="success">激活</el-tag>
          <el-tag v-else type="info">未激活</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="success" @click="handleActivate(row)">激活</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑配置' : '创建配置'" width="520px">
      <el-form @submit.prevent="handleSubmit">
        <el-form-item label="配置名称">
          <el-input v-model="form.name" placeholder="如 DeepSeek Default" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Qwen（通义千问）" value="qwen" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.model" placeholder="如 deepseek-chat" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password
            :placeholder="isEditing ? '留空则不修改' : 'sk-xxx'" />
        </el-form-item>
        <el-form-item label="API 端点（可选）">
          <el-input v-model="form.base_url"
            :placeholder="form.provider === 'deepseek' ? '默认 https://api.deepseek.com' : form.provider === 'qwen' ? '默认 https://dashscope.aliyuncs.com/compatible-mode/v1' : '默认 https://api.openai.com/v1'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.llm-config { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
