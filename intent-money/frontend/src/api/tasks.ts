import request from './index'

export function getIntents() {
  return request.get('/intents')
}

export function getPlatforms() {
  return request.get('/platforms')
}

export function createTask(data: Record<string, unknown>) {
  return request.post('/tasks', data)
}

export function getCurrentTask(platformId?: string) {
  const params: Record<string, string> = {}
  if (platformId) params.platform_id = platformId
  return request.get('/tasks/current', { params })
}

export function getTask(taskId: string) {
  return request.get(`/tasks/${taskId}`)
}

export function publishTask(taskId: string) {
  return request.post(`/tasks/${taskId}/publish`)
}

export function reportTask(taskId: string, data: Record<string, unknown>) {
  return request.post(`/tasks/${taskId}/report`, data)
}

export function getDiagnosis(taskId: string) {
  return request.get(`/tasks/${taskId}/diagnosis`)
}

export function getNextTask(taskId: string, data: Record<string, unknown>) {
  return request.post(`/tasks/${taskId}/next`, data)
}

export function swapTask(taskId: string) {
  return request.post(`/tasks/${taskId}/swap`)
}

export function getTaskHistory(params?: Record<string, string>) {
  return request.get('/tasks/history', { params })
}

export function getAdminStats() {
  return request.get('/admin/stats')
}

export function getContentStructures() {
  return request.get('/content-structures')
}

export function updateContentStructure(id: string, data: Record<string, unknown>) {
  return request.put(`/content-structures/${id}`, data)
}

export function getConversionPaths(intentId?: string) {
  const params: Record<string, string> = {}
  if (intentId) params.intent_id = intentId
  return request.get('/conversion-paths', { params })
}

export function createConversionPath(data: Record<string, unknown>) {
  return request.post('/conversion-paths', data)
}

export function updateConversionPath(id: string, data: Record<string, unknown>) {
  return request.put(`/conversion-paths/${id}`, data)
}

export function deleteConversionPath(id: string) {
  return request.delete(`/conversion-paths/${id}`)
}

export function getMarketHots(platformId?: string) {
  const params: Record<string, string> = {}
  if (platformId) params.platform_id = platformId
  return request.get('/market/hots', { params })
}

export function createMarketHot(data: Record<string, unknown>) {
  return request.post('/market/hots', data)
}

export function analyzeMarket(platformId: string) {
  return request.post('/market/analyze', { platform_id: platformId })
}

export function updateMarketScores() {
  return request.post('/market/update-scores')
}

export function getEvolutionStats() {
  return request.get('/admin/evolution/stats')
}

export function adjustRuleWeights() {
  return request.post('/admin/evolution/adjust-weights')
}

export function autoPublish(taskId: string) {
  return request.post(`/publish/${taskId}/auto`)
}

export function uploadCookie(data: Record<string, unknown>) {
  return request.post('/publish/cookie', data)
}

export function checkCookieStatus(platform: string) {
  return request.get(`/publish/cookie/${platform}`)
}
