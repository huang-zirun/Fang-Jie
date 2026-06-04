import request from './index'

export interface AccountInfo {
  id: string
  platform: string
  platform_user_id: string | null
  platform_nickname: string | null
  platform_avatar: string | null
  cookie_status: string
  cookie_set_at: string | null
  cookie_expires_at: string | null
  last_validated_at: string | null
  bind_status: string
  bind_method: string | null
  created_at: string | null
}

export function getAccounts() {
  return request.get<AccountInfo[]>('/accounts/')
}

export function importCookie(platform: string, cookieData: string) {
  return request.post<AccountInfo>(`/accounts/${platform}/cookie`, { cookie_data: cookieData })
}

export function validateAccount(platform: string) {
  return request.post(`/accounts/${platform}/validate`)
}

export function unbindAccount(platform: string) {
  return request.delete(`/accounts/${platform}`)
}

export function requestQrCode(platform: string) {
  return request.post('/accounts/' + platform + '/qrcode')
}

export function checkQrCodeStatus(platform: string, sessionId: string) {
  return request.get(`/accounts/${platform}/qrcode/${sessionId}/status`)
}

export function extensionCookieLogin(platform: string, cookies: Array<Record<string, any>>) {
  return request.post<AccountInfo>(`/accounts/${platform}/extension`, { cookies })
}
