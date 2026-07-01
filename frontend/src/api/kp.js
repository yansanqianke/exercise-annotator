/** 知识点管理 API 调用 */
import request from './request'

/** 获取知识点列表（可按学科过滤） */
export function getKPsApi(subjectId) {
  const params = subjectId ? { subject_id: subjectId } : {}
  return request.get('/kps', { params }).then((r) => r.data)
}

/** 创建知识点 */
export function createKPApi(data) {
  return request.post('/kps', data).then((r) => r.data)
}

/** 更新知识点 */
export function updateKPApi(id, data) {
  return request.put(`/kps/${id}`, data).then((r) => r.data)
}

/** 删除知识点 */
export function deleteKPApi(id) {
  return request.delete(`/kps/${id}`)
}

/** 获取相似知识点推荐 */
export function getSimilarKPsApi(id, topK = 5) {
  return request.get(`/kps/${id}/similar`, { params: { top_k: topK } }).then((r) => r.data)
}
