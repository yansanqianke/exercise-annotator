<!-- 题目标注页 — 题目导入 + 知识点解析 -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getKPsApi, createKPApi } from '../../api/kp'
import { getQuestionsApi, getQuestionApi, updateQuestionKPsApi, deleteQuestionApi } from '../../api/question'

// ===== 状态 =====
const subjects = ref([])
const subjectFilter = ref(null)
const questionText = ref('')
const questions = ref([])
const annotatingId = ref(null)
const reasoning = ref('')
const result = ref(null)
const saveLoading = ref(false)

// 手动修正
const editDialogVisible = ref(false)
const editingQuestion = ref(null)
const allKPs = ref([])
const selectedKPs = ref([])

// 选中的题目（左侧展示）
const selectedQuestion = ref(null)

// ===== 题目列表（右侧） =====
async function loadQuestions() {
  const params = {}
  if (subjectFilter.value) params.subject_id = subjectFilter.value
  questions.value = await getQuestionsApi(params)
}

// ===== 题目导入 =====
async function saveOnly() {
  if (!questionText.value.trim() || !subjectFilter.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  saveLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    await fetch('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ content: questionText.value, subject_id: subjectFilter.value }),
    })
    ElMessage.success('已保存到题库')
    questionText.value = ''
    loadQuestions()
  } finally { saveLoading.value = false }
}

async function saveAndAnnotate() {
  if (!questionText.value.trim() || !subjectFilter.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  doAnnotate({ content: questionText.value, subject_id: subjectFilter.value })
}

// ===== 知识点解析（左侧） =====
async function annotateQuestion(row) {
  selectedQuestion.value = row
  reasoning.value = ''
  result.value = null
  annotatingId.value = row.id

  const token = localStorage.getItem('access_token')
  try {
    const res = await fetch('/api/agent/annotate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ question_id: row.id, subject_id: row.subject_id }),
    })
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || '请求失败')

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
            else if (event.type === 'done') { ElMessage.success('标注完成'); loadQuestions() }
            else if (event.type === 'error') ElMessage.error(event.content)
          } catch { /* */ }
        }
      }
    }
  } catch (err) {
    ElMessage.error(err.message)
  } finally {
    annotatingId.value = null
    // 刷新选中题目数据
    if (selectedQuestion.value) {
      selectedQuestion.value = await getQuestionApi(selectedQuestion.value.id)
    }
  }
}

// ===== 手动修正 =====
async function openEdit(row) {
  editingQuestion.value = row
  allKPs.value = await getKPsApi(row.subject_id)
  selectedKPs.value = row.kp_maps?.map(k => k.kp_id) || []
  editDialogVisible.value = true
}
async function saveEdit() {
  await updateQuestionKPsApi(editingQuestion.value.id, selectedKPs.value.map(id => ({ kp_id: id })))
  ElMessage.success('知识点已更新')
  editDialogVisible.value = false
  loadQuestions()
}

// ===== 删除 =====
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确认删除该题目？', '确认删除', { type: 'warning' })
    await deleteQuestionApi(row.id)
    if (selectedQuestion.value?.id === row.id) selectedQuestion.value = null
    ElMessage.success('已删除'); loadQuestions()
  } catch { /* */ }
}

// ===== 建议 KP =====
async function confirmSuggestKp(index) {
  const s = result.value?.suggest_kps?.[index]
  const qid = result.value?.question_id
  if (!s || !qid) return
  try {
    const q = await getQuestionApi(qid)
    const newKp = await createKPApi({ subject_id: q.subject_id, name: s.name, description: s.description })
    const ids = (q.kp_maps || []).map(k => ({ kp_id: k.kp_id }))
    ids.push({ kp_id: newKp.id })
    await updateQuestionKPsApi(qid, ids)
    ElMessage.success(`"${s.name}" 已创建并关联`)
    result.value.suggest_kps.splice(index, 1)
    loadQuestions()
  } catch { /* */ }
}

function onFilterChange() { loadQuestions() }

onMounted(async () => {
  subjects.value = await getSubjectsApi()
  loadQuestions()
})
</script>

<template>
  <div class="annotate-layout">
    <!-- ===== 左侧：标注工作区 ===== -->
    <div class="annotate-main">
      <!-- 题目导入卡片 -->
      <div class="import-card">
        <div class="card-label">题目导入</div>
        <div class="import-row">
          <el-select v-model="subjectFilter" placeholder="选择学科" size="large">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>
        <el-input v-model="questionText" type="textarea" :rows="4" placeholder="输入题目内容，例如：给定一个单链表，请编写函数反转链表。要求时间复杂度 O(n)，空间复杂度 O(1)。" />
        <div class="import-actions">
          <el-button @click="saveOnly" :loading="saveLoading" :disabled="!subjectFilter">保存到题库</el-button>
          <el-button type="primary" @click="saveAndAnnotate" :disabled="!subjectFilter || annotatingId !== null">保存并立即标注</el-button>
        </div>
      </div>

      <!-- 标注结果区 -->
      <div v-if="selectedQuestion" class="work-area">
        <div class="card-label">标注详情 #{{ selectedQuestion.id }}</div>

        <!-- 题目原文 -->
        <div class="question-preview">{{ selectedQuestion.content }}</div>

        <!-- 标注状态 -->
        <div v-if="selectedQuestion.type && selectedQuestion.difficulty" class="quick-tags">
          <span class="qt-tag type">{{ selectedQuestion.type }}</span>
          <span class="qt-tag diff">难度 {{ selectedQuestion.difficulty }}/5</span>
          <span v-for="k in selectedQuestion.kp_maps" :key="k.kp_id" class="qt-tag kp">{{ k.knowledge_point.code }}</span>
        </div>

        <!-- 推理过程 -->
        <div v-if="reasoning" class="reasoning-block">
          <div class="block-title">推理过程</div>
          <pre class="reasoning-text">{{ reasoning }}</pre>
        </div>

        <!-- 标注结果 -->
        <div v-if="result" class="result-block">
          <div class="block-title">本次标注结果</div>
          <div class="result-grid">
            <div class="rg-item"><span>题型</span><strong>{{ result.question_type }}</strong></div>
            <div class="rg-item"><span>难度</span><strong>{{ result.difficulty }} / 5</strong></div>
          </div>
          <div class="result-kps">
            <span class="rg-label">知识点</span>
            <el-tag v-for="code in result.kp_codes" :key="code" size="small" style="margin-right:6px">{{ code }}</el-tag>
            <span v-if="!result.kp_codes?.length" style="color:var(--color-text-muted);font-size:13px">无匹配知识点</span>
          </div>
          <div v-if="result.reasoning" class="result-reasoning">
            <span class="rg-label">依据</span>{{ result.reasoning }}
          </div>

          <!-- 建议新 KP -->
          <div v-if="result.suggest_kps?.length" class="suggest-card">
            <div class="suggest-title">建议新增知识点（教师确认后入库）</div>
            <div v-for="(sug, i) in result.suggest_kps" :key="i" class="suggest-row">
              <div>
                <strong>{{ sug.name }}</strong>
                <span class="sug-desc">{{ sug.description }}</span>
              </div>
              <el-button size="small" type="success" @click="confirmSuggestKp(i)">确认入库</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-work">
        <div class="empty-icon">✦</div>
        <p>从右侧题库中选择一道题目<br>点击"标注"开始知识点解析</p>
      </div>
    </div>

    <!-- ===== 右侧：题库列表 ===== -->
    <div class="annotate-sidebar">
      <div class="list-header">
        <span class="list-title">题库</span>
        <el-select v-model="subjectFilter" placeholder="按学科筛选" clearable size="small" @change="onFilterChange" style="width:160px">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </div>

      <div class="question-list">
        <div
          v-for="q in questions" :key="q.id"
          :class="['q-item', { selected: selectedQuestion?.id === q.id }]"
          @click="selectedQuestion = q"
        >
          <div class="q-meta">
            <span v-if="q.type" class="q-type">{{ q.type }}</span>
            <span v-if="q.difficulty" class="q-diff">难度{{ q.difficulty }}</span>
            <span v-else class="q-unlabeled">未标注</span>
          </div>
          <div class="q-content">{{ q.content }}</div>
          <div v-if="q.kp_maps?.length" class="q-kps">
            <span v-for="k in q.kp_maps" :key="k.kp_id" class="q-kp">{{ k.knowledge_point.code }}</span>
          </div>
          <div class="q-actions" @click.stop>
            <el-button
              size="small" type="primary" plain
              :loading="annotatingId === q.id"
              @click="annotateQuestion(q)"
            >标注</el-button>
            <el-button size="small" @click="openEdit(q)">修正</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(q)">删除</el-button>
          </div>
        </div>
        <div v-if="!questions.length" class="q-empty">暂无题目</div>
      </div>
    </div>

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
.annotate-layout {
  display: flex;
  height: 100%;
  gap: 0;
}
.annotate-main {
  flex: 1;
  padding: var(--space-lg);
  overflow-y: auto;
  min-width: 0;
}
.annotate-sidebar {
  width: 380px;
  border-left: 1px solid var(--color-border);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* ===== 导入卡片 ===== */
.import-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}
.card-label {
  font-family: var(--font-heading);
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: .04em;
}
.import-row { margin-bottom: var(--space-sm); }
.import-actions {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: var(--space-sm);
}

/* ===== 工作区 ===== */
.work-area { }
.question-preview {
  padding: var(--space-md);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: 15px;
  line-height: 1.7;
  margin-bottom: var(--space-md);
  border: 1px solid var(--color-border-light);
}
.quick-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: var(--space-md); }
.qt-tag {
  font-size: 12px; padding: 3px 10px; border-radius: 12px; font-weight: 500;
}
.qt-tag.type { background: #e8f0e8; color: #5b8c5a; }
.qt-tag.diff { background: #faf0e0; color: #c4872b; }
.qt-tag.kp { background: #e8ecf6; color: #3d5a99; }

/* 推理 */
.reasoning-block { margin-bottom: var(--space-md); }
.block-title {
  font-family: var(--font-heading);
  font-size: 14px; font-weight: 600; margin-bottom: 8px;
}
.reasoning-text {
  padding: var(--space-md);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.6;
  max-height: 240px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border: 1px solid var(--color-border-light);
}

/* 结果 */
.result-block { margin-bottom: var(--space-md); }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.rg-item { padding: var(--space-sm) var(--space-md); background: var(--color-bg); border-radius: var(--radius-sm); font-size: 14px; display: flex; justify-content: space-between; }
.rg-item span { color: var(--color-text-secondary); }
.result-kps, .result-reasoning { padding: var(--space-sm) var(--space-md); margin-bottom: 6px; font-size: 14px; }
.rg-label { font-size: 12px; color: var(--color-text-muted); margin-right: 8px; display: inline-block; min-width: 48px; }

/* 建议 */
.suggest-card {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: #fdf8f0;
  border-radius: var(--radius-sm);
  border: 1px solid #f0e0c0;
}
.suggest-title { font-size: 13px; font-weight: 600; color: var(--color-warning); margin-bottom: 8px; }
.suggest-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid #f0e0c0;
}
.suggest-row:last-child { border-bottom: none; }
.sug-desc { display: block; font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }

/* 空状态 */
.empty-work {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 300px; color: var(--color-text-muted);
}
.empty-icon { font-size: 48px; margin-bottom: var(--space-md); color: var(--color-accent); opacity: .6; }
.empty-work p { text-align: center; line-height: 1.6; font-size: 14px; }

/* ===== 右侧列表 ===== */
.list-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.list-title {
  font-family: var(--font-heading); font-size: 15px; font-weight: 600;
}
.question-list {
  flex: 1; overflow-y: auto; padding: var(--space-sm);
}
.q-item {
  padding: var(--space-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: 6px;
  border: 1px solid transparent;
  transition: all .15s;
}
.q-item:hover { background: var(--color-bg); }
.q-item.selected { border-color: var(--color-primary); background: #f0f3fa; }
.q-meta { display: flex; gap: 6px; margin-bottom: 6px; }
.q-type, .q-diff {
  font-size: 11px; padding: 1px 6px; border-radius: 8px; background: var(--color-bg);
  color: var(--color-text-secondary);
}
.q-unlabeled { font-size: 11px; color: var(--color-accent); }
.q-content {
  font-size: 13px; line-height: 1.5; color: var(--color-text);
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 6px;
}
.q-kps { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 6px; }
.q-kp {
  font-size: 11px; padding: 1px 6px; background: #e8ecf6; color: #3d5a99;
  border-radius: 4px;
}
.q-actions { display: flex; gap: 4px; }
.q-empty { text-align: center; color: var(--color-text-muted); padding: var(--space-xl); font-size: 14px; }
</style>
