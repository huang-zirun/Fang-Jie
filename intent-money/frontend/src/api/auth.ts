import request from './index'

export function anonymousRegister() {
  return request.post('/auth/anonymous')
}

export function login(phone: string, code: string) {
  return request.post('/auth/login', { phone, code })
}
