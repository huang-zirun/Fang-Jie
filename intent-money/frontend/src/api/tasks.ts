import request from './index'

export function getIntents() {
  return request.get('/intents')
}

export function createTask(data: Record<string, unknown>) {
  return request.post('/tasks', data)
}

export function getCurrentTask() {
  return request.get('/tasks/current')
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
