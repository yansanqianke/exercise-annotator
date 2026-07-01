/** LLM 配置管理 API 调用 */
import request from './request'

/** 获取配置列表 */
export function getLLMConfigsApi() {
  return request.get('/llm-configs').then((r) => r.data)
}

/** 创建配置 */
export function createLLMConfigApi(data) {
  return request.post('/llm-configs', data).then((r) => r.data)
}

/** 更新配置 */
export function updateLLMConfigApi(id, data) {
  return request.put(`/llm-configs/${id}`, data).then((r) => r.data)
}

/** 激活配置 */
export function activateLLMConfigApi(id) {
  return request.put(`/llm-configs/${id}/activate`).then((r) => r.data)
}

/** 删除配置 */
export function deleteLLMConfigApi(id) {
  return request.delete(`/llm-configs/${id}`)
}
