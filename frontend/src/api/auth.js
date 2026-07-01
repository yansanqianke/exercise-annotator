/** 认证相关 API 调用 */
import request from './request'

/** 用户登录 */
export function loginApi(username, password) {
  return request.post('/auth/login', { username, password }).then((r) => r.data)
}

/** 用户注册 */
export function registerApi(username, email, password) {
  return request.post('/auth/register', { username, email, password }).then((r) => r.data)
}

/** 获取当前用户信息 */
export function getMeApi() {
  return request.get('/auth/me').then((r) => r.data)
}

/** 修改个人信息（邮箱 / 密码） */
export function updateMeApi(data) {
  return request.put('/auth/me', data).then((r) => r.data)
}
