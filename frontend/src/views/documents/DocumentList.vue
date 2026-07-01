<!-- 文档管理页面 -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getDocumentsApi, uploadDocumentApi, indexDocumentApi, extractQuestionsApi } from '../../api/document'

const subjects = ref([])
const documents = ref([])
const selectedSubject = ref(null)
const uploadDialog = ref(false)
const uploadForm = ref({ file: null, doc_type: 'reference', subject_id: null })
const uploading = ref(false)

async function loadSubjects() {
  subjects.value = await getSubjectsApi()
}

async function loadDocuments() {
  const params = {}
  if (selectedSubject.value) params.subject_id = selectedSubject.value
  documents.value = await getDocumentsApi(params)
}

function onSubjectChange() { loadDocuments() }

async function handleUpload() {
  if (!uploadForm.value.file || !uploadForm.value.subject_id) {
    ElMessage.warning('请选择文件和学科')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadForm.value.file)
    fd.append('doc_type', uploadForm.value.doc_type)
    fd.append('subject_id', uploadForm.value.subject_id)

    const result = await uploadDocumentApi(fd)
    ElMessage.success(`上传成功: ${result.original_name}`)
    uploadDialog.value = false
    loadDocuments()
  } catch { /* 拦截器处理 */ }
  finally { uploading.value = false }
}

async function handleIndex(row) {
  try {
    const result = await indexDocumentApi(row.id)
    ElMessage.success(`索引完成: ${result.chunks} 个分块`)
    loadDocuments()
  } catch { /* */ }
}

async function handleExtract(row) {
  try {
    const result = await extractQuestionsApi(row.id)
    const count = result.saved || result.questions?.length || 0
    ElMessage.success(`提取完成：识别 ${result.questions?.length || 0} 题，已入库 ${count} 题`)
    loadDocuments()
  } catch { /* */ }
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw
}

onMounted(() => {
  loadSubjects()
  loadDocuments()
})
</script>

<template>
  <div class="doc-page">
    <div class="header">
      <h2>文档管理</h2>
      <div class="header-actions">
        <el-select v-model="selectedSubject" placeholder="按学科筛选" clearable style="width: 200px" @change="onSubjectChange">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button type="primary" @click="uploadDialog = true">上传文档</el-button>
      </div>
    </div>

    <el-table :data="documents" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="original_name" label="文件名" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.doc_type === 'reference'" type="info">参考资料</el-tag>
          <el-tag v-else type="warning">题目文档</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'done'" type="success">已完成</el-tag>
          <el-tag v-else-if="row.status === 'processing'" type="warning">处理中</el-tag>
          <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
          <el-tag v-else type="info">待处理</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.doc_type === 'reference' && row.status !== 'done'" size="small" type="success" @click="handleIndex(row)">索引</el-button>
          <el-button v-if="row.doc_type === 'questions' && row.status !== 'done'" size="small" type="warning" @click="handleExtract(row)">提取题目</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialog" title="上传文档" width="450px">
      <el-form>
        <el-form-item label="文档类型">
          <el-radio-group v-model="uploadForm.doc_type">
            <el-radio value="reference">参考资料（索引到向量库）</el-radio>
            <el-radio value="questions">题目文档（提取题目列表）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="uploadForm.subject_id" placeholder="选择学科" style="width: 100%">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" drag>
            <el-button type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word、PPT、TXT 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.doc-page { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-actions { display: flex; gap: 12px; }
</style>
