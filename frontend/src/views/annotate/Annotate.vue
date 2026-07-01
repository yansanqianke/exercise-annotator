<!-- 题目标注页面 — 题目导入 + 知识点解析 -->
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getKPsApi, createKPApi } from '../../api/kp'
import { getQuestionsApi, getQuestionApi, updateQuestionKPsApi, deleteQuestionApi } from '../../api/question'
import { useSSE } from '../../composables/useSSE'

// ===== 题目导入 =====
const subjects = ref([])
const selectedSubject = ref(null)
const questionText = ref('')
const importLoading = ref(false)

/** 仅保存题目到题库（不触发标注） */
async function saveOnly() {
  if (!questionText.value.trim() || !selectedSubject.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  importLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    await fetch('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ content: questionText.value, subject_id: selectedSubject.value }),
    })
    ElMessage.success('题目已保存到题库')
    questionText.value = ''
    loadQuestions()
  } catch { /* */ }
  finally { importLoading.value = false }
}

/** 保存并立即标注 */
async function saveAndAnnotate() {
  if (!questionText.value.trim() || !selectedSubject.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  doAnnotate({ content: questionText.value, subject_id: selectedSubject.value })
}

// ===== 知识点解析 =====
const questions = ref([])
/** 正在标注的题目 ID（用于行内 loading 状态） */
const annotatingId = ref(null)
/** 推理过程文本 */
const reasoning = ref('')
/** 标注结果 */
const result = ref(null)

/** SSE 标注 — 支持新题目和已有题目 */
async function doAnnotate(bodyOrQuestion) {
  reasoning.value = ''
  result.value = null

  let body
  if (typeof bodyOrQuestion === 'object' && bodyOrQuestion.id) {
    // 已有题目
    body = { question_id: bodyOrQuestion.id, subject_id: bodyOrQuestion.subject_id }
    annotatingId.value = bodyOrQuestion.id
  } else {
    // 新题目
    body = bodyOrQuestion
    annotatingId.value = null
  }

  const token = localStorage.getItem('access_token')
  try {
    const res = await fetch('/api/agent/annotate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'thinking') reasoning.value += event.content
            else if (event.type === 'result') result.value = event
            else if (event.type === 'done') {
              ElMessage.success('标注完成')
              loadQuestions()
              questionText.value = ''
            }
            else if (event.type === 'error') ElMessage.error(event.content)
          } catch { /* */ }
        }
      }
    }
  } catch (err) {
    ElMessage.error(err.message)
  } finally {
    annotatingId.value = null
  }
}

// ===== 题库列表 =====
async function loadQuestions() {
  const params = {}
  if (selectedSubject.value) params.subject_id = selectedSubject.value
  questions.value = await getQuestionsApi(params)
}

const filterSubject = ref(null)
function onFilterChange() {
  loadQuestions()
}

// ===== 手动修正 =====
const editDialogVisible = ref(false)
const editingQuestion = ref(null)
const allKPs = ref([])
const selectedKPs = ref([])

async function openEdit(question) {
  editingQuestion.value = question
  allKPs.value = await getKPsApi(question.subject_id)
  selectedKPs.value = question.kp_maps?.map(k => k.kp_id) || []
  editDialogVisible.value = true
}

async function saveEdit() {
  await updateQuestionKPsApi(editingQuestion.value.id, selectedKPs.value.map(id => ({ kp_id: id })))
  ElMessage.success('知识点已更新')
  editDialogVisible.value = false
  loadQuestions()
}

/** 删除题目 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确认删除该题目？', '确认删除', { type: 'warning' })
    await deleteQuestionApi(row.id)
    ElMessage.success('已删除')
    loadQuestions()
  } catch { /* */ }
}

// ===== 建议 KP 确认 =====
async function confirmSuggestKp(index) {
  const s = result.value?.suggest_kps?.[index]
  const questionId = result.value?.question_id
  if (!s || !questionId) return
  try {
    const newKp = await createKPApi({
      subject_id: selectedSubject.value || questions.value.find(q => q.id === questionId)?.subject_id,
      name: s.name,
      description: s.description,
    })
    const question = await getQuestionApi(questionId)
    const existingKpIds = (question.kp_maps || []).map(k => ({ kp_id: k.kp_id }))
    existingKpIds.push({ kp_id: newKp.id })
    await updateQuestionKPsApi(questionId, existingKpIds)
    ElMessage.success(`知识点 "${s.name}" 已创建并关联到题目`)
    result.value.suggest_kps.splice(index, 1)
    loadQuestions()
  } catch { /* */ }
}

onMounted(() => {
  loadSubjects()
  loadQuestions()
})
</script>

<template>
  <div class="annotate-page">
    <h2>题目标注</h2>

    <!-- ========== 模块一：题目导入 ========== -->
    <el-card class="section-card">
      <template #header><h3>题目导入</h3></template>
      <div class="import-row">
        <el-select v-model="selectedSubject" placeholder="选择学科" style="width: 200px">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </div>
      <el-input
        v-model="questionText"
        type="textarea"
        :rows="4"
        placeholder="输入题目内容..."
        style="margin-top: 12px"
      />
      <div class="import-actions">
        <el-button @click="saveOnly" :loading="importLoading">保存到题库</el-button>
        <el-button type="primary" @click="saveAndAnnotate" :disabled="annotatingId !== null">
          保存并立即标注
        </el-button>
      </div>
    </el-card>

    <!-- ========== 推理过程 ========== -->
    <el-card v-if="reasoning" class="section-card">
      <template #header>推理过程</template>
      <pre class="reasoning-text">{{ reasoning }}</pre>
    </el-card>

    <!-- ========== 标注结果 ========== -->
    <el-card v-if="result" class="section-card" style="border-color: #67c23a">
      <template #header>标注结果</template>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="题型">{{ result.question_type }}</el-descriptions-item>
        <el-descriptions-item label="难度">{{ result.difficulty }} / 5</el-descriptions-item>
        <el-descriptions-item label="知识点" :span="2">
          <el-tag v-for="code in result.kp_codes" :key="code" style="margin-right: 8px">{{ code }}</el-tag>
          <span v-if="!result.kp_codes?.length" style="color:#999">无匹配知识点</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="result.reasoning" label="依据" :span="2">{{ result.reasoning }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="result.suggest_kps?.length" class="suggest-section">
        <h4>建议新增知识点（教师确认后入库）</h4>
        <div v-for="(sug, i) in result.suggest_kps" :key="i" class="suggest-item">
          <div class="suggest-info">
            <strong>{{ sug.name }}</strong>
            <span class="suggest-desc">{{ sug.description }}</span>
          </div>
          <el-button size="small" type="success" @click="confirmSuggestKp(i)">确认入库</el-button>
        </div>
      </div>
    </el-card>

    <!-- ========== 模块二：题库列表 ========== -->
    <el-card class="section-card">
      <template #header>
        <div class="list-header">
          <h3>题库列表</h3>
          <el-select v-model="filterSubject" placeholder="按学科筛选" clearable style="width:200px" @change="onFilterChange">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>
      </template>
      <el-table :data="questions" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="content" label="题目" show-overflow-tooltip />
        <el-table-column prop="type" label="题型" width="110" />
        <el-table-column prop="difficulty" label="难度" width="70">
          <template #default="{ row }">
            <span v-if="row.difficulty">{{ row.difficulty }}</span>
            <el-tag v-else size="small" type="info">未标注</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="知识点" width="200">
          <template #default="{ row }">
            <el-tag v-for="k in row.kp_maps" :key="k.kp_id" size="small" style="margin:2px">
              {{ k.knowledge_point.code }}
            </el-tag>
            <span v-if="!row.kp_maps?.length" style="color:#999;font-size:12px">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary"
              :loading="annotatingId === row.id"
              @click="doAnnotate(row)">
              标注
            </el-button>
            <el-button size="small" @click="openEdit(row)">修正</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 手动修正对话框 -->
    <el-dialog v-model="editDialogVisible" title="手动修正知识点" width="500px">
      <el-select v-model="selectedKPs" multiple placeholder="选择知识点" style="width:100%">
        <el-option v-for="k in allKPs" :key="k.id" :label="`${k.code}: ${k.name}`" :value="k.id" />
      </el-select>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.annotate-page { padding: 24px; max-width: 960px; margin: 0 auto; }
.section-card { margin-bottom: 16px; }
.import-row { display: flex; gap: 12px; }
.import-actions { margin-top: 12px; display: flex; justify-content: flex-end; gap: 8px; }
.list-header { display: flex; justify-content: space-between; align-items: center; }
.list-header h3 { margin: 0; }
.reasoning-text { white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 14px; }
.suggest-section { margin-top: 16px; padding: 12px; background: #fdf6ec; border-radius: 8px; border: 1px solid #faecd8; }
.suggest-section h4 { margin: 0 0 8px; color: #e6a23c; font-size: 14px; }
.suggest-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #faecd8; }
.suggest-item:last-child { border-bottom: none; }
.suggest-info { display: flex; flex-direction: column; }
.suggest-desc { font-size: 12px; color: #999; margin-top: 2px; }
</style>
