<!-- 题目导入页 — 手动输入 + 文档批量提取 -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { uploadDocumentApi, extractQuestionsApi } from '../../api/document'

const subjects = ref([])
const selectedSubject = ref(null)
const questionText = ref('')
const saveLoading = ref(false)

// ===== 文档提取 =====
const extractFile = ref(null)
const extractLoading = ref(false)
const extractResult = ref(null)

onMounted(async () => { subjects.value = await getSubjectsApi() })

/** 手动保存 */
async function saveManual() {
  if (!questionText.value.trim() || !selectedSubject.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  saveLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    await fetch('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ content: questionText.value, subject_id: selectedSubject.value }),
    })
    ElMessage.success('题目已保存到题库')
    questionText.value = ''
  } finally { saveLoading.value = false }
}

/** 文档提取 */
async function doExtract() {
  if (!extractFile.value || !selectedSubject.value) {
    ElMessage.warning('请选择学科和文件')
    return
  }
  extractLoading.value = true
  try {
    const fd = new FormData()
    fd.append('file', extractFile.value)
    fd.append('doc_type', 'questions')
    fd.append('subject_id', selectedSubject.value)
    const doc = await uploadDocumentApi(fd)
    const result = await extractQuestionsApi(doc.id)
    extractResult.value = result
    ElMessage.success(`提取完成：提取 ${result.questions?.length || 0} 题，入库 ${result.saved || 0} 题`)
  } catch { /* */ }
  finally { extractLoading.value = false }
}

function handleFileChange(file) { extractFile.value = file.raw }
</script>

<template>
  <div class="import-page">
    <!-- 学科选择 -->
    <div class="subject-bar">
      <span class="bar-label">目标学科</span>
      <el-select v-model="selectedSubject" placeholder="选择学科" size="large" style="width:240px">
        <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </div>

    <div class="import-columns">
      <!-- 手动输入 -->
      <div class="import-card">
        <div class="card-title">手动输入</div>
        <el-input v-model="questionText" type="textarea" :rows="8"
          placeholder="输入题目内容..." :disabled="!selectedSubject" />
        <div class="card-actions">
          <span class="char-count">{{ questionText.length }} 字</span>
          <el-button type="primary" @click="saveManual" :loading="saveLoading" :disabled="!selectedSubject">
            保存到题库
          </el-button>
        </div>
      </div>

      <!-- 文档提取 -->
      <div class="import-card">
        <div class="card-title">文档批量提取</div>
        <p class="card-desc">上传 PDF / Word / PPT / TXT，LLM 自动识别题目并入库</p>
        <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" drag
          :disabled="!selectedSubject" style="width:100%">
          <div class="upload-area">
            <span class="upload-icon">📄</span>
            <p>点击或拖拽文件到此区域</p>
            <p class="upload-hint">支持 PDF、Word、PPT、TXT</p>
          </div>
        </el-upload>
        <div class="card-actions">
          <el-button type="primary" @click="doExtract" :loading="extractLoading" :disabled="!extractFile || !selectedSubject">
            上传并提取
          </el-button>
        </div>

        <!-- 提取结果 -->
        <div v-if="extractResult" class="extract-result">
          <div class="result-summary">
            识别 <strong>{{ extractResult.questions?.length || 0 }}</strong> 题，
            已入库 <strong>{{ extractResult.saved || 0 }}</strong> 题
          </div>
          <div v-for="(q, i) in extractResult.questions" :key="i" class="extract-item">
            <span class="extract-idx">{{ i + 1 }}</span>
            <span class="extract-content">{{ q.content }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-page { padding: var(--space-lg); max-width: 1100px; }
.subject-bar { display: flex; align-items: center; gap: 12px; margin-bottom: var(--space-lg); }
.bar-label { font-family: var(--font-heading); font-weight: 600; font-size: 15px; }

.import-columns { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-lg); }
.import-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}
.card-title {
  font-family: var(--font-heading); font-size: 16px; font-weight: 600; margin-bottom: 12px;
}
.card-desc { font-size: 13px; color: var(--color-text-muted); margin-bottom: 12px; }
.card-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.char-count { font-size: 12px; color: var(--color-text-muted); }

.upload-area { display: flex; flex-direction: column; align-items: center; padding: 24px; cursor: pointer; }
.upload-icon { font-size: 36px; margin-bottom: 8px; }
.upload-area p { font-size: 14px; color: var(--color-text-secondary); }
.upload-hint { font-size: 12px !important; color: var(--color-text-muted) !important; margin-top: 4px; }

.extract-result { margin-top: var(--space-md); border-top: 1px solid var(--color-border-light); padding-top: var(--space-md); }
.result-summary { font-size: 14px; margin-bottom: 8px; }
.extract-item { display: flex; gap: 8px; padding: 6px 0; font-size: 13px; border-bottom: 1px solid var(--color-border-light); }
.extract-idx { color: var(--color-text-muted); min-width: 24px; }
.extract-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
