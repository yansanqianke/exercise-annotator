/** Vue Router 路由配置 — 含角色路由守卫 */
import { createRouter, createWebHistory } from 'vue-router'

/** 路由定义 — 暂时只有认证相关页面，后续逐步添加 */
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/subjects',
    name: 'Subjects',
    component: () => import('../views/subjects/SubjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge-points',
    name: 'KnowledgePoints',
    component: () => import('../views/kps/KPList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/chat/Chat.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/llm-config',
    name: 'LLMConfig',
    component: () => import('../views/admin/LLMConfig.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    // 未匹配路由重定向到首页
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/** 全局前置守卫 — 检查登录状态与角色权限 */
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')

  // 需要登录的页面
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  // 已登录用户访问 guest 页面（登录/注册）时重定向到首页
  if (to.meta.guest && token) {
    return next('/')
  }

  // admin 专属页面检查角色
  if (to.meta.requiresAdmin) {
    // 从 JWT payload 解析角色（简单 base64 解码）
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.role !== 'admin') {
        return next('/')
      }
    } catch {
      return next('/login')
    }
  }

  next()
})

export default router
