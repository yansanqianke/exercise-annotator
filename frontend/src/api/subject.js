/** 学科管理 API 调用 */
import request from './request'

/** 获取学科列表 */
export function getSubjectsApi() {
  return request.get('/subjects').then((r) => r.data)
}

/** 创建学科 */
export function createSubjectApi(data) {
  return request.post('/subjects', data).then((r) => r.data)
}

/** 更新学科 */
export function updateSubjectApi(id, data) {
  return request.put(`/subjects/${id}`, data).then((r) => r.data)
}

/** 删除学科 */
export function deleteSubjectApi(id) {
  return request.delete(`/subjects/${id}`)
}
