/** Vue Router 路由配置 — 含角色路由守卫 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/auth/Login.vue'), meta: { guest: true, title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('../views/auth/Register.vue'), meta: { guest: true, title: '注册' } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { requiresAuth: true, title: '首页' } },
  { path: '/subjects', name: 'Subjects', component: () => import('../views/subjects/SubjectList.vue'), meta: { requiresAuth: true, title: '学科管理' } },
  { path: '/knowledge-points', name: 'KnowledgePoints', component: () => import('../views/kps/KPList.vue'), meta: { requiresAuth: true, title: '知识点管理' } },
  { path: '/import', name: 'QuestionImport', component: () => import('../views/import/QuestionImport.vue'), meta: { requiresAuth: true, title: '题目导入' } },
  { path: '/questions', name: 'Questions', component: () => import('../views/questions/QuestionList.vue'), meta: { requiresAuth: true, title: '题目管理' } },
  { path: '/documents', name: 'Documents', component: () => import('../views/documents/DocumentList.vue'), meta: { requiresAuth: true, title: '参考资料' } },
  { path: '/annotate', redirect: '/questions' },
  { path: '/chat', name: 'Chat', component: () => import('../views/chat/Chat.vue'), meta: { requiresAuth: true, title: 'AI 对话' } },
  { path: '/admin/users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' } },
  { path: '/admin/agents', name: 'AdminAgents', component: () => import('../views/admin/Agents.vue'), meta: { requiresAuth: true, requiresAdmin: true, title: '智能体管理' } },
  { path: '/admin/logs', name: 'AdminLogs', component: () => import('../views/admin/Logs.vue'), meta: { requiresAuth: true, requiresAdmin: true, title: '系统日志' } },
  { path: '/admin/llm-config', name: 'LLMConfig', component: () => import('../views/admin/LLMConfig.vue'), meta: { requiresAuth: true, requiresAdmin: true, title: '大模型配置' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.guest && token) return next('/')

  if (to.meta.requiresAdmin) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.role !== 'admin') return next('/')
    } catch { return next('/login') }
  }

  next()
})

export default router
