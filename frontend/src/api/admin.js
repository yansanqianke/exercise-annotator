/** 管理后台 API 调用 */
import request from './request'

// ===== 用户管理 =====
export function getUsersApi() {
  return request.get('/admin/users').then(r => r.data)
}
export function updateUserRoleApi(id, role) {
  return request.put(`/admin/users/${id}/role`, { role }).then(r => r.data)
}
export function updateUserActiveApi(id, isActive) {
  return request.put(`/admin/users/${id}/active`, { is_active: isActive }).then(r => r.data)
}

// ===== 智能体管理 =====
export function getAgentsApi() {
  return request.get('/admin/agents').then(r => r.data)
}
export function createAgentApi(data) {
  return request.post('/admin/agents', data).then(r => r.data)
}
export function updateAgentApi(id, data) {
  return request.put(`/admin/agents/${id}`, data).then(r => r.data)
}

// ===== 系统日志 =====
export function getLogsApi(params) {
  return request.get('/admin/logs', { params }).then(r => r.data)
}
