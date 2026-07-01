/** 题目管理 API 调用 */
import request from './request'

/** 获取题目列表 */
export function getQuestionsApi(params) {
  return request.get('/questions', { params }).then((r) => r.data)
}

/** 获取题目详情 */
export function getQuestionApi(id) {
  return request.get(`/questions/${id}`).then((r) => r.data)
}

/** 手动修正知识点 */
export function updateQuestionKPsApi(id, kps) {
  return request.put(`/questions/${id}/kps`, kps).then((r) => r.data)
}

/** 删除题目 */
export function deleteQuestionApi(id) {
  return request.delete(`/questions/${id}`)
}
