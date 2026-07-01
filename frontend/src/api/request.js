/** axios 实例 — 自动附加 JWT Token，统一错误处理 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 — 从 localStorage 读取 token 附加到 Authorization 头
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器 — 处理 401 跳转登录页
request.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('access_token')
      router.push('/login')
    }
    ElMessage.error(error.response?.data?.detail || '请求失败')
    return Promise.reject(error)
  },
)

export default request
