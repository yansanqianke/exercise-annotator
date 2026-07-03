/** 文档管理 API 调用 */
import request from './request'

/** 上传文档 */
export function uploadDocumentApi(formData) {
  return request.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

/** 获取文档列表 */
export function getDocumentsApi(params) {
  return request.get('/documents', { params: { ...params, doc_type: 'reference' } }).then((r) => r.data)
}

/** 索引参考资料 */
export function indexDocumentApi(id) {
  return request.post(`/documents/${id}/index`).then((r) => r.data)
}

/** 提取题目 */
export function extractQuestionsApi(id) {
  return request.post(`/documents/${id}/extract`).then((r) => r.data)
}
