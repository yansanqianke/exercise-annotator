<!-- 知识点管理页面 -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getKPsApi, createKPApi, updateKPApi, deleteKPApi, getSimilarKPsApi } from '../../api/kp'

/** 数据 */
const subjects = ref([])
const kps = ref([])
const selectedSubject = ref(null)
const loading = ref(false)

/** 创建 / 编辑对话框 */
const dialogVisible = ref(false)
const isEditing = ref(false)
const form = ref({ id: null, subject_id: null, name: '', description: '' })

/** 相似知识点对话框 */
const similarDialogVisible = ref(false)
const similarKPs = ref([])
const currentKpName = ref('')

/** 加载学科列表（用于筛选） */
async function loadSubjects() {
  subjects.value = await getSubjectsApi()
}

/** 加载知识点列表 */
async function loadKPs() {
  loading.value = true
  try {
    kps.value = await getKPsApi(selectedSubject.value)
  } finally {
    loading.value = false
  }
}

/** 学科筛选变化时重新加载 */
function onSubjectChange() {
  loadKPs()
}

/** 打开创建对话框 */
function openCreate() {
  if (!selectedSubject.value) {
    ElMessage.warning('请先选择学科')
    return
  }
  isEditing.value = false
  form.value = { id: null, subject_id: selectedSubject.value, name: '', description: '' }
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
      await updateKPApi(form.value.id, {
        name: form.value.name,
        description: form.value.description,
      })
      ElMessage.success('知识点已更新')
    } else {
      await createKPApi({
        subject_id: form.value.subject_id,
        name: form.value.name,
        description: form.value.description,
      })
      ElMessage.success('知识点已创建')
    }
    dialogVisible.value = false
    await loadKPs()
  } catch { /* 拦截器已处理 */ }
}

/** 删除知识点 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除知识点 "${row.name}"？`, '确认删除', { type: 'warning' })
    await deleteKPApi(row.id)
    ElMessage.success('已删除')
    await loadKPs()
  } catch { /* 取消或失败 */ }
}

import { ElMessageBox } from 'element-plus'

/** 查看相似知识点 */
async function showSimilar(row) {
  currentKpName.value = row.name
  similarKPs.value = await getSimilarKPsApi(row.id, 5)
  similarDialogVisible.value = true
}

onMounted(() => {
  loadSubjects()
  loadKPs()
})
</script>

<template>
  <div class="kp-list">
    <div class="header">
      
      <div class="header-actions">
        <el-select
          v-model="selectedSubject"
          placeholder="按学科筛选"
          clearable
          style="width: 200px"
          @change="onSubjectChange"
        >
          <el-option
            v-for="s in subjects"
            :key="s.id"
            :label="s.name"
            :value="s.id"
          />
        </el-select>
        <el-button type="primary" @click="openCreate">创建知识点</el-button>
      </div>
    </div>

    <el-table :data="kps" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="code" label="编码" width="130" />
      <el-table-column prop="name" label="知识点名称" width="180" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="is_deleted" label="状态" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.is_deleted" type="danger">已删除</el-tag>
          <el-tag v-else type="success">正常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="showSimilar(row)">相似推荐</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建 / 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑知识点' : '创建知识点'" width="500px">
      <el-form @submit.prevent="handleSubmit">
        <el-form-item label="知识点名称">
          <el-input v-model="form.name" placeholder="如 链表" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="知识点详细描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 相似知识点对话框 -->
    <el-dialog v-model="similarDialogVisible" :title="`与「${currentKpName}」相似的知识点`" width="450px">
      <el-table :data="similarKPs" border>
        <el-table-column prop="code" label="编码" width="130" />
        <el-table-column prop="distance" label="相似度" width="100">
          <template #default="{ row }">
            {{ row.distance?.toFixed(4) || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.kp-list { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-actions { display: flex; gap: 12px; }
</style>
