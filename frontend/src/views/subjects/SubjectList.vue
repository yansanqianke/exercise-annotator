<!-- 学科管理页面 -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubjectsApi, createSubjectApi, updateSubjectApi, deleteSubjectApi } from '../../api/subject'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const subjects = ref([])
const loading = ref(false)

/** 创建 / 编辑对话框状态 */
const dialogVisible = ref(false)
const isEditing = ref(false)
const form = ref({ id: null, code: '', name: '', description: '' })

/** 加载学科列表 */
async function loadSubjects() {
  loading.value = true
  try {
    subjects.value = await getSubjectsApi()
  } finally {
    loading.value = false
  }
}

/** 打开创建对话框 */
function openCreate() {
  isEditing.value = false
  form.value = { id: null, code: '', name: '', description: '' }
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEdit(row) {
  isEditing.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

/** 提交表单 */
async function handleSubmit() {
  try {
    if (isEditing.value) {
      await updateSubjectApi(form.value.id, {
        name: form.value.name,
        description: form.value.description,
      })
      ElMessage.success('学科已更新')
    } else {
      await createSubjectApi({
        code: form.value.code,
        name: form.value.name,
        description: form.value.description,
      })
      ElMessage.success('学科已创建')
    }
    dialogVisible.value = false
    await loadSubjects()
  } catch { /* 拦截器已处理 */ }
}

/** 删除学科 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除学科 "${row.name}"？`, '确认删除', { type: 'warning' })
    await deleteSubjectApi(row.id)
    ElMessage.success('已删除')
    await loadSubjects()
  } catch { /* 取消或失败 */ }
}

onMounted(loadSubjects)
</script>

<template>
  <div class="subject-list">
    <div class="header">
      
      <el-button type="primary" @click="openCreate">创建学科</el-button>
    </div>

    <el-table :data="subjects" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="code" label="学科代码" width="120" />
      <el-table-column prop="name" label="学科名称" />
      <el-table-column prop="description" label="简介" show-overflow-tooltip />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="authStore.isAdmin"
            size="small"
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建 / 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑学科' : '创建学科'" width="500px">
      <el-form @submit.prevent="handleSubmit">
        <el-form-item v-if="!isEditing" label="学科代码">
          <el-input v-model="form.code" placeholder="如 DS、OS" />
        </el-form-item>
        <el-form-item label="学科名称">
          <el-input v-model="form.name" placeholder="如 数据结构" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" placeholder="学科简介（选填）" />
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
.subject-list { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
