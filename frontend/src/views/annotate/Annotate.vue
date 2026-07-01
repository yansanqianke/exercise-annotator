<!-- 题目标注页面（核心功能） -->
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSubjectsApi } from '../../api/subject'
import { getKPsApi } from '../../api/kp'
import { getQuestionsApi, updateQuestionKPsApi } from '../../api/question'
import { useSSE } from '../../composables/useSSE'

const { isStreaming, start, abort } = useSSE()

/** 学科列表 */
const subjects = ref([])
/** 当前选中的学科 */
const selectedSubject = ref(null)
/** 题目输入 */
const questionText = ref('')
/** 推理过程（文本累积） */
const reasoning = ref('')
/** 标注结果 */
const result = ref(null)
/** 已标注的题目列表 */
const questions = ref([])

/** 手动修正对话框 */
const editDialogVisible = ref(false)
const editingQuestion = ref(null)
const allKPs = ref([])
const selectedKPs = ref([])

/** 加载学科列表 */
async function loadSubjects() {
  subjects.value = await getSubjectsApi()
}

/** 开始标注 */
async function startAnnotate() {
  if (!questionText.value.trim() || !selectedSubject.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  reasoning.value = ''
  result.value = null

  await start('/agent/annotate', {
    content: questionText.value,
    subject_id: selectedSubject.value,
  }, {
    onThinking(chunk) {
      reasoning.value += chunk
    },
    onDone() {
      ElMessage.success('标注完成')
      loadQuestions()
    },
    onError(msg) {
      ElMessage.error(msg)
    },
  })

  // 解析 result 事件
  // 需要从 SSE 流中捕获 result — 暂时通过轮询方式
}

/** 标注 SSE 请求（重写 — 解析 result 事件） */
async function doAnnotate() {
  if (!questionText.value.trim() || !selectedSubject.value) {
    ElMessage.warning('请选择学科并输入题目')
    return
  }
  reasoning.value = ''
  result.value = null

  const token = localStorage.getItem('access_token')
  const controller = new AbortController()

  try {
    const res = await fetch('/api/agent/annotate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({
        content: questionText.value,
        subject_id: selectedSubject.value,
      }),
      signal: controller.signal,
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
            }
            else if (event.type === 'error') ElMessage.error(event.content)
          } catch { /* skip */ }
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') ElMessage.error(err.message)
  }
}

/** 加载已标注题目 */
async function loadQuestions() {
  const params = {}
  if (selectedSubject.value) params.subject_id = selectedSubject.value
  questions.value = await getQuestionsApi(params)
}

/** 打开手动修正对话框 */
async function openEdit(question) {
  editingQuestion.value = question
  allKPs.value = await getKPsApi(question.subject_id)
  selectedKPs.value = question.kp_maps?.map(k => k.kp_id) || []
  editDialogVisible.value = true
}

/** 保存手动修正 */
async function saveEdit() {
  await updateQuestionKPsApi(editingQuestion.value.id, selectedKPs.value.map(id => ({ kp_id: id })))
  ElMessage.success('知识点已更新')
  editDialogVisible.value = false
  loadQuestions()
}

onMounted(() => {
  loadSubjects()
  loadQuestions()
})
</script>

<template>
  <div class="annotate-page">
    <h2>题目标注</h2>

    <!-- 标注输入区 -->
    <el-card class="input-card">
      <div class="input-row">
        <el-select v-model="selectedSubject" placeholder="选择学科" style="width: 200px">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </div>
      <el-input
        v-model="questionText"
        type="textarea"
        :rows="5"
        placeholder="输入题目内容，例如：&#10;给定一个单链表，请编写函数反转链表。要求时间复杂度 O(n)，空间复杂度 O(1)。"
        style="margin-top: 12px"
      />
      <div class="action-row">
        <el-button type="primary" size="large" @click="doAnnotate" :loading="isStreaming">
          开始标注
        </el-button>
      </div>
    </el-card>

    <!-- 推理过程 -->
    <el-card v-if="reasoning" class="reasoning-card">
      <template #header>推理过程</template>
      <pre class="reasoning-text">{{ reasoning }}</pre>
    </el-card>

    <!-- 标注结果 -->
    <el-card v-if="result" class="result-card" type="success">
      <template #header>标注结果</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="题型">{{ result.question_type }}</el-descriptions-item>
        <el-descriptions-item label="难度">{{ result.difficulty }} / 5</el-descriptions-item>
        <el-descriptions-item label="知识点" :span="2">
          <el-tag v-for="code in result.kp_codes" :key="code" style="margin-right: 8px">
            {{ code }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="result.reasoning" label="依据" :span="2">
          {{ result.reasoning }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 已标注题目列表 -->
    <el-card class="questions-card">
      <template #header>已标注题目</template>
      <el-table :data="questions" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="content" label="题目" show-overflow-tooltip />
        <el-table-column prop="type" label="题型" width="110" />
        <el-table-column prop="difficulty" label="难度" width="70" />
        <el-table-column label="知识点" width="200">
          <template #default="{ row }">
            <el-tag v-for="k in row.kp_maps" :key="k.kp_id" size="small" style="margin: 2px">
              {{ k.kp_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">修正</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 手动修正对话框 -->
    <el-dialog v-model="editDialogVisible" title="手动修正知识点" width="500px">
      <el-select v-model="selectedKPs" multiple placeholder="选择知识点" style="width: 100%">
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
.annotate-page { padding: 24px; max-width: 900px; margin: 0 auto; }
.input-card { margin-bottom: 16px; }
.input-row { display: flex; gap: 12px; }
.action-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.reasoning-card { margin-bottom: 16px; }
.reasoning-text { white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 14px; }
.result-card { margin-bottom: 16px; }
.questions-card { margin-top: 16px; }
</style>
