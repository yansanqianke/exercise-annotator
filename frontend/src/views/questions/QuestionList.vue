<!-- 题目管理页 — 题库列表 + 标注 + 批量操作 -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getKPsApi, createKPApi } from '../../api/kp'
import { getQuestionsApi, getQuestionApi, updateQuestionKPsApi, deleteQuestionApi } from '../../api/question'
import { InfoFilled } from '@element-plus/icons-vue'

// ===== 状态 =====
const subjects = ref([])
const questions = ref([])
const filterSubject = ref(null)
const filterType = ref(null)
const loading = ref(false)

// 选中
const selectedIds = ref(new Set())
const currentQuestion = ref(null)

// 标注
const annotatingIds = ref(new Set())
const reasoning = ref('')
const result = ref(null)

// 修正对话框
const editDialogVisible = ref(false)
const editingQuestion = ref(null)
const allKPs = ref([])
const selectedKPs = ref([])

// 分页
const page = ref(1)
const pageSize = 20

const filteredQuestions = computed(() => {
  let qs = questions.value
  if (filterSubject.value) qs = qs.filter(q => q.subject_id === filterSubject.value)
  if (filterType.value) qs = qs.filter(q => q.type === filterType.value)
  return qs
})

const displayedQuestions = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredQuestions.value.slice(start, start + pageSize)
})

const total = computed(() => filteredQuestions.value.length)

// ===== 加载 =====
async function load() {
  loading.value = true
  try { questions.value = await getQuestionsApi({}) }
  finally { loading.value = false }
}

// ===== 选择 =====
function toggleSelect(id) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}
function selectAll() {
  if (selectedIds.value.size === displayedQuestions.value.length)
    selectedIds.value = new Set()
  else
    selectedIds.value = new Set(displayedQuestions.value.map(q => q.id))
}

// ===== 标注 =====
function selectQuestion(q) {
  currentQuestion.value = q
  reasoning.value = ''
  result.value = null
}
async function annotateCurrent() {
  if (!currentQuestion.value) return
  const q = currentQuestion.value
  annotatingIds.value.add(q.id)
  reasoning.value = ''
  result.value = null

  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/agent/annotate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ question_id: q.id, subject_id: q.subject_id }),
    })
    if (!res.ok) throw new Error('请求失败')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      for (const line of buffer.split('\n\n')) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'thinking') reasoning.value += event.content
            else if (event.type === 'result') result.value = event
            else if (event.type === 'done') { ElMessage.success('标注完成'); load() }
            else if (event.type === 'error') ElMessage.error(event.content)
          } catch { /* */ }
        }
      }
    }
  } catch (e) { ElMessage.error(e.message) }
  finally {
    annotatingIds.value.delete(q.id)
    currentQuestion.value = await getQuestionApi(q.id)
  }
}

// ===== 导出 =====
async function doExport(fmt) {
  const token = localStorage.getItem('access_token')
  const params = new URLSearchParams()
  params.set('fmt', fmt)
  if (selectedIds.value.size > 0) params.set('ids', [...selectedIds.value].join(','))
  if (filterSubject.value) params.set('subject_id', filterSubject.value)

  try {
    const res = await fetch(`/api/questions/export?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '导出失败' }))
      ElMessage.error(err.detail)
      return
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `questions.${fmt}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

// ===== 批量标注 =====
async function batchAnnotate() {
  if (selectedIds.value.size === 0) { ElMessage.warning('请先选择题目'); return }
  const ids = [...selectedIds.value]
  let done = 0
  for (const id of ids) {
    const q = questions.value.find(q => q.id === id)
    if (!q) continue
    try {
      const token = localStorage.getItem('access_token')
      await fetch('/api/agent/annotate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ question_id: id, subject_id: q.subject_id }),
      })
    } catch { /* 单题失败不中断 */ }
    done++
  }
  ElMessage.success(`批量标注完成：${done}/${ids.length}`)
  selectedIds.value = new Set()
  load()
}

// ===== 修正 =====
async function openEdit(q) {
  editingQuestion.value = q
  allKPs.value = await getKPsApi(q.subject_id)
  selectedKPs.value = q.kp_maps?.map(k => k.kp_id) || []
  editDialogVisible.value = true
}
async function saveEdit() {
  await updateQuestionKPsApi(editingQuestion.value.id, selectedKPs.value.map(id => ({ kp_id: id })))
  ElMessage.success('知识点已更新')
  editDialogVisible.value = false
  load()
}

// ===== 删除 =====
async function handleDelete(q) {
  try {
    await ElMessageBox.confirm('确认删除？', '确认删除', { type: 'warning' })
    await deleteQuestionApi(q.id)
    if (currentQuestion.value?.id === q.id) currentQuestion.value = null
    load()
  } catch { /* */ }
}
async function batchDelete() {
  if (selectedIds.value.size === 0) { ElMessage.warning('请先选择题目'); return }
  try {
    await ElMessageBox.confirm(`确认删除 ${selectedIds.value.size} 道题目？`, '批量删除', { type: 'warning' })
    for (const id of selectedIds.value) {
      await deleteQuestionApi(id).catch(() => {})
    }
    selectedIds.value = new Set()
    load()
  } catch { /* */ }
}

// ===== 建议 KP =====
async function confirmSuggestKp(index) {
  const s = result.value?.suggest_kps?.[index]
  const qid = result.value?.question_id
  if (!s || !qid) return
  const q = await getQuestionApi(qid)
  const newKp = await createKPApi({ subject_id: q.subject_id, name: s.name, description: s.description })
  const ids = (q.kp_maps || []).map(k => ({ kp_id: k.kp_id }))
  ids.push({ kp_id: newKp.id })
  await updateQuestionKPsApi(qid, ids)
  ElMessage.success(`"${s.name}" 已创建并关联`)
  result.value.suggest_kps.splice(index, 1)
  load()
}

const typeOptions = [
  { label: '选择题', value: 'choice' },
  { label: '判断题', value: 'judgment' },
  { label: '简答题', value: 'short_answer' },
  { label: '编程题', value: 'programming' },
]

onMounted(async () => {
  subjects.value = await getSubjectsApi()
  load()
})
</script>

<template>
  <div class="q-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-filters">
        <el-select v-model="filterSubject" placeholder="学科" clearable size="default" style="width:160px">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-select v-model="filterType" placeholder="题型" clearable size="default" style="width:140px">
          <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      </div>
      <div class="toolbar-actions">
        <el-button :disabled="selectedIds.size === 0" @click="batchAnnotate">批量标注 ({{ selectedIds.size }})</el-button>
        <el-button :disabled="selectedIds.size === 0" type="danger" plain @click="batchDelete">批量删除</el-button>
        <el-dropdown @command="doExport" style="margin-left:8px">
          <el-button>导出 <el-icon style="margin-left:4px"><arrow-down /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="q-layout">
      <!-- 左侧：题目表格 -->
      <div class="q-table-area">
        <el-table :data="displayedQuestions" v-loading="loading" border
          @row-click="selectQuestion" highlight-current-row size="small">
          <el-table-column width="40">
            <template #default="{ row }">
              <el-checkbox :model-value="selectedIds.has(row.id)" @change="toggleSelect(row.id)" @click.stop />
            </template>
          </el-table-column>
          <el-table-column prop="id" label="ID" width="50" />
          <el-table-column prop="content" label="题目" show-overflow-tooltip min-width="200" />
          <el-table-column prop="type" label="题型" width="90">
            <template #default="{ row }">
              <span v-if="row.type" class="type-badge">{{ {choice:'选择',judgment:'判断',short_answer:'简答',programming:'编程'}[row.type] }}</span>
              <span v-else class="unlabeled">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="difficulty" label="难度" width="60">
            <template #default="{ row }">{{ row.difficulty || '—' }}</template>
          </el-table-column>
          <el-table-column label="知识点" width="140">
            <template #default="{ row }">
              <span v-for="k in row.kp_maps" :key="k.kp_id" class="kp-chip">{{ k.knowledge_point.code }}</span>
              <span v-if="!row.kp_maps?.length" class="unlabeled">—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" plain
                :loading="annotatingIds.has(row.id)"
                @click.stop="selectQuestion(row); annotateCurrent()">标注</el-button>
              <el-button size="small" @click.stop="openEdit(row)">修正</el-button>
              <el-button size="small" type="danger" plain @click.stop="handleDelete(row)">删</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination">
          <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev,next,total" small />
        </div>
      </div>

      <!-- 右侧：标注详情面板 -->
      <div class="q-detail">
        <template v-if="currentQuestion">
          <div class="detail-header">
            <span class="detail-title">题目 #{{ currentQuestion.id }}</span>
          </div>
          <div class="detail-content">{{ currentQuestion.content }}</div>

          <div v-if="currentQuestion.type" class="detail-meta">
            <span class="meta-badge type">{{ {choice:'选择题',judgment:'判断题',short_answer:'简答题',programming:'编程题'}[currentQuestion.type] }}</span>
            <span v-if="currentQuestion.difficulty" class="meta-badge diff">难度 {{ currentQuestion.difficulty }}</span>
            <span v-for="k in currentQuestion.kp_maps" :key="k.kp_id" class="meta-badge kp">{{ k.knowledge_point.code }}</span>
          </div>

          <div v-if="result" class="detail-result">
            <div class="section-label">标注结果</div>
            <div class="result-row"><span>题型</span><strong>{{ result.question_type }}</strong></div>
            <div class="result-row"><span>难度</span><strong>{{ result.difficulty }}/5</strong></div>
            <div class="result-row"><span>知识点</span><strong>{{ result.kp_codes?.join(', ') || '无' }}</strong></div>

            <div v-if="result.suggest_kps?.length" class="suggest-box">
              <div class="suggest-title">建议新知识点</div>
              <div v-for="(sug, i) in result.suggest_kps" :key="i" class="suggest-row">
                <div><strong>{{ sug.name }}</strong><span class="sug-desc">{{ sug.description }}</span></div>
                <el-button size="small" type="success" @click="confirmSuggestKp(i)">入库</el-button>
              </div>
            </div>
          </div>

          <el-button type="primary" :loading="annotatingIds.has(currentQuestion.id)" @click="annotateCurrent" style="width:100%;margin-top:12px">
            {{ currentQuestion.type ? '重新标注' : '开始标注' }}
          </el-button>
        </template>
        <div v-else class="detail-empty">
          <el-icon :size="36"><InfoFilled /></el-icon>
          <p>点击左侧题目查看详情</p>
        </div>
      </div>
    </div>

    <!-- 修正对话框 -->
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
.q-page { display: flex; flex-direction: column; height: 100%; }
.toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px var(--space-lg); background: var(--color-surface);
  border-bottom: 1px solid var(--color-border); flex-shrink: 0;
}
.toolbar-filters { display: flex; gap: 8px; }
.toolbar-actions { display: flex; gap: 8px; }

.q-layout { display: flex; flex: 1; min-height: 0; }
.q-table-area { flex: 1; overflow-y: auto; padding: var(--space-md); min-width: 0; }
.q-detail {
  width: 360px; border-left: 1px solid var(--color-border);
  background: var(--color-surface); overflow-y: auto; padding: var(--space-lg);
  flex-shrink: 0;
}

.type-badge {
  font-size: 11px; padding: 1px 6px; border-radius: 8px;
  background: var(--color-bg); color: var(--color-text-secondary);
}
.unlabeled { font-size: 12px; color: var(--color-text-muted); }
.kp-chip {
  font-size: 10px; padding: 1px 4px; background: #e8ecf6; color: #3d5a99;
  border-radius: 3px; margin: 1px;
}
.pagination { padding: 12px 0; display: flex; justify-content: flex-end; }

/* 详情面板 */
.detail-header { margin-bottom: 12px; }
.detail-title { font-family: var(--font-heading); font-weight: 600; font-size: 15px; }
.detail-content {
  padding: 12px; background: var(--color-bg); border-radius: var(--radius-sm);
  font-size: 14px; line-height: 1.7; margin-bottom: 12px;
}
.detail-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.meta-badge { font-size: 12px; padding: 3px 10px; border-radius: 12px; }
.meta-badge.type { background: #e8f0e8; color: #5b8c5a; }
.meta-badge.diff { background: #faf0e0; color: #c4872b; }
.meta-badge.kp { background: #e8ecf6; color: #3d5a99; }

.section-label { font-family: var(--font-heading); font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.detail-reasoning { margin-bottom: 12px; }
.reasoning-text {
  padding: 12px; background: var(--color-bg); border-radius: var(--radius-sm);
  font-size: 12px; line-height: 1.5; max-height: 200px; overflow-y: auto;
  white-space: pre-wrap; word-break: break-word;
}
.detail-result { margin-bottom: 12px; }
.result-row {
  display: flex; justify-content: space-between; padding: 6px 12px;
  background: var(--color-bg); border-radius: 4px; margin-bottom: 4px; font-size: 13px;
}
.result-row span { color: var(--color-text-secondary); }

.suggest-box {
  margin-top: 8px; padding: 12px; background: #fdf8f0;
  border-radius: var(--radius-sm); border: 1px solid #f0e0c0;
}
.suggest-title { font-size: 12px; font-weight: 600; color: var(--color-warning); margin-bottom: 6px; }
.suggest-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid #f0e0c0; font-size: 13px;
}
.suggest-row:last-child { border-bottom: none; }
.sug-desc { display: block; font-size: 11px; color: var(--color-text-muted); margin-top: 2px; }

.detail-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 200px; color: var(--color-text-muted);
}
.detail-empty .el-icon { margin-bottom: 8px; color: var(--color-accent); opacity: .4; }
</style>
