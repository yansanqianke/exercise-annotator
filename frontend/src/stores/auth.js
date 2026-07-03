/** Pinia 认证状态管理 — 存储当前用户信息与 Token */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getMeApi, updateMeApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  /** 当前登录用户信息（null 表示未登录） */
  const user = ref(null)
  /** JWT 访问令牌 */
  const token = ref(localStorage.getItem('access_token') || '')

  /** 是否已登录 */
  const isLoggedIn = computed(() => !!token.value)
  /** 是否为管理员 */
  const isAdmin = computed(() => user.value?.role === 'admin')

  /** 用户登录 */
  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.access_token
    localStorage.setItem('access_token', res.access_token)
    await fetchUser()
  }

  /** 用户注册（注册成功自动登录） */
  async function register(username, email, password) {
    const res = await registerApi(username, email, password)
    token.value = res.access_token
    localStorage.setItem('access_token', res.access_token)
    await fetchUser()
  }

  /** 获取当前用户信息 */
  async function fetchUser() {
    user.value = await getMeApi()
  }

  /** 更新个人信息 */
  async function updateProfile(data) {
    user.value = await updateMeApi(data)
  }

  /** 初始化 — 若已有 token 则拉取用户信息（用于刷新后恢复状态） */
  async function init() {
    if (token.value && !user.value) {
      try {
        await fetchUser()
      } catch {
        logout()
      }
    }
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, isLoggedIn, isAdmin, login, register, fetchUser, updateProfile, logout, init }
})
