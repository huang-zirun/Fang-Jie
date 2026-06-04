<template>
  <div class="account-page">
    <CyberNav title="账号管理" />

    <div class="account-content">
      <div class="section-title">已绑定平台</div>

      <div v-if="extensionChecking" class="login-hint">
        <van-loading size="14" color="#00f5d4" />
        <span>正在检测浏览器扩展...</span>
      </div>
      <div v-else-if="extensionInstalled" class="login-hint extension-connected">
        <van-icon name="checked" size="14" color="#00f5d4" />
        <span>扩展已连接，支持一键登录和Cookie获取</span>
      </div>
      <div v-else class="login-hint extension-missing">
        <van-icon name="info-o" size="14" color="#ffd60a" />
        <span>未检测到浏览器扩展，将使用扫码登录。安装扩展可支持一键登录。</span>
      </div>

      <div v-for="platform in platforms" :key="platform.key" class="account-card" :class="{ 'card-bound': isBound(platform.key) }">
        <div class="card-header">
          <div class="platform-icon" :style="{ background: platform.color }">
            <span>{{ platform.icon }}</span>
          </div>
          <div class="platform-info">
            <div class="platform-name">{{ platform.name }}</div>
            <div class="platform-status">
              <span class="status-dot" :class="getStatusClass(platform.key)"></span>
              <span class="status-text">{{ getStatusText(platform.key) }}</span>
              <span v-if="extensionInstalled && extensionStatus[platform.key]?.loggedIn" class="ext-status-badge">
                浏览器已登录
              </span>
            </div>
          </div>
        </div>

        <div v-if="isBound(platform.key)" class="card-detail">
          <div class="detail-row" v-if="getAccount(platform.key)?.platform_nickname">
            <span class="detail-label">昵称</span>
            <span class="detail-value">{{ getAccount(platform.key)?.platform_nickname }}</span>
          </div>
          <div class="detail-row" v-if="getAccount(platform.key)?.cookie_expires_at">
            <span class="detail-label">过期时间</span>
            <span class="detail-value" :class="{ 'text-warning': isExpiringSoon(platform.key) }">
              {{ formatDate(getAccount(platform.key)?.cookie_expires_at) }}
            </span>
          </div>
          <div class="detail-row" v-if="getAccount(platform.key)?.last_validated_at">
            <span class="detail-label">最后验证</span>
            <span class="detail-value">{{ formatDate(getAccount(platform.key)?.last_validated_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn-action btn-primary" @click="handleOneClickLogin(platform.key)">一键登录</button>
          <button v-if="extensionInstalled && extensionStatus[platform.key]?.loggedIn && !isBound(platform.key)" class="btn-action btn-secondary" @click="handleFetchCookies(platform.key)">同步到后端</button>
          <button v-if="isBound(platform.key)" class="btn-action btn-outline" @click="handleValidate(platform.key)">验证</button>
          <button v-if="isBound(platform.key)" class="btn-action btn-danger" @click="handleUnbind(platform.key)">解绑</button>
        </div>
      </div>

      <div v-if="accounts.length === 0" class="empty-state">
        <p>暂未绑定任何平台账号</p>
        <p class="empty-hint">导入Cookie或扫码登录后即可抓取爆款数据</p>
      </div>
    </div>

    <van-dialog v-model:show="qrDialogVisible" :title="qrPlatformName + ' 扫码登录'" :show-confirm-button="false" width="90%">
      <div class="dialog-content qr-content">
        <div v-if="qrLoading" class="qr-loading">
          <van-loading size="48px">加载中...</van-loading>
        </div>
        <div v-else-if="qrCodeUrl" class="qr-image-wrapper">
          <img :src="qrCodeUrl" alt="QR Code" class="qr-image" />
          <p class="qr-tip">请使用{{ qrPlatformName }}APP扫描二维码</p>
        </div>
        <div v-else-if="qrStatus === 'confirmed'" class="qr-success">
          <van-icon name="checked" size="48" color="#00f5d4" />
          <p>登录成功</p>
        </div>
        <div v-else-if="qrStatus === 'expired'" class="qr-expired">
          <van-icon name="warning-o" size="48" color="#ff006e" />
          <p>二维码已过期</p>
          <button class="btn-action btn-primary" @click="retryQrLogin">重新获取</button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import CyberNav from '../components/CyberNav.vue'
import { getAccounts, validateAccount, unbindAccount, requestQrCode, checkQrCodeStatus, extensionCookieLogin, type AccountInfo } from '../api/accounts'

const accounts = ref<AccountInfo[]>([])
const qrDialogVisible = ref(false)
const qrCodeUrl = ref('')
const qrLoading = ref(false)
const qrStatus = ref('')
const qrSessionId = ref('')
const qrPlatform = ref('')
const extensionInstalled = ref(false)
const extensionChecking = ref(true)
let qrPollTimer: ReturnType<typeof setInterval> | null = null
const extensionStatus = reactive<Record<string, { loggedIn: boolean; cookieCount: number; timestamp: number }>>({})
let checkExtensionTimeout: ReturnType<typeof setTimeout> | null = null
let currentAttempt = 0
const maxAttempts = 5
const retryDelays = [1000, 2000, 3000, 4000, 5000]

const platforms = [
  { key: 'xhs', name: '小红书', icon: '📕', color: '#ff2442' },
  { key: 'douyin', name: '抖音', icon: '🎵', color: '#161823' },
]

const qrPlatformName = computed(() => {
  return platforms.find(p => p.key === qrPlatform.value)?.name || ''
})

onMounted(() => {
  fetchAccounts()
  checkExtension()
  window.addEventListener('message', onGlobalMessage)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  stopQrPoll()
  if (checkExtensionTimeout) {
    clearTimeout(checkExtensionTimeout)
    checkExtensionTimeout = null
  }
  window.removeEventListener('message', onGlobalMessage)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

async function fetchAccounts() {
  try {
    const res = await getAccounts()
    accounts.value = res.data || []
  } catch {
    showToast('获取账号列表失败')
  }
}

function getAccount(platformKey: string): AccountInfo | undefined {
  return accounts.value.find(a => a.platform === platformKey)
}

function isBound(platformKey: string): boolean {
  const account = getAccount(platformKey)
  return !!account && account.bind_status === 'bound'
}

function getStatusClass(platformKey: string): string {
  const account = getAccount(platformKey)
  if (!account) return 'status-unbound'
  if (account.cookie_status === 'active') return 'status-active'
  if (account.cookie_status === 'expired') return 'status-expired'
  return 'status-pending'
}

function getStatusText(platformKey: string): string {
  const account = getAccount(platformKey)
  if (!account) return '未绑定'
  const map: Record<string, string> = {
    active: '正常',
    expired: '已过期',
    invalid: '无效',
    pending: '待验证',
  }
  return map[account.cookie_status] || account.cookie_status
}

function isExpiringSoon(platformKey: string): boolean {
  const account = getAccount(platformKey)
  if (!account?.cookie_expires_at) return false
  const expiresAt = new Date(account.cookie_expires_at)
  const twoDaysLater = new Date()
  twoDaysLater.setDate(twoDaysLater.getDate() + 2)
  return expiresAt < twoDaysLater
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function checkExtension() {
  if (extensionInstalled.value) return
  extensionChecking.value = true
  currentAttempt = 0
  if (checkExtensionTimeout) {
    clearTimeout(checkExtensionTimeout)
    checkExtensionTimeout = null
  }
  doCheckExtension()
}

function doCheckExtension() {
  if (extensionInstalled.value) {
    extensionChecking.value = false
    return
  }
  if (currentAttempt >= maxAttempts) {
    extensionInstalled.value = false
    extensionChecking.value = false
    return
  }

  const attemptTimeout = setTimeout(() => {
    window.removeEventListener('message', handler)
    currentAttempt++
    if (currentAttempt >= maxAttempts) {
      extensionInstalled.value = false
      extensionChecking.value = false
    } else {
      const delay = retryDelays[currentAttempt - 1] || 1000
      checkExtensionTimeout = setTimeout(doCheckExtension, delay)
    }
  }, 2000)

  function handler(event: MessageEvent) {
    if (event.data?.type === 'INTENT_MONEY_PONG') {
      clearTimeout(attemptTimeout)
      window.removeEventListener('message', handler)
      extensionInstalled.value = true
      extensionChecking.value = false
      configureExtension()
    }
  }
  window.addEventListener('message', handler)
  window.postMessage({ type: 'INTENT_MONEY_PING' }, '*')
}

function onGlobalMessage(event: MessageEvent) {
  if (event.data?.type === 'INTENT_MONEY_STATUS_UPDATE') {
    const platform = event.data.platform
    if (platform) {
      // 映射扩展平台名称到前端平台键名
      const platformKeyMap: Record<string, string> = {
        xiaohongshu: 'xhs',
        douyin: 'douyin'
      }
      const platformKey = platformKeyMap[platform] || platform
      // 使用 Object.assign 确保响应式更新
      Object.assign(extensionStatus, {
        [platformKey]: {
          loggedIn: !!event.data.loggedIn,
          cookieCount: event.data.cookieCount || 0,
          timestamp: event.data.timestamp || Date.now(),
        }
      })
      // 同步成功后刷新账号列表
      fetchAccounts()
    }
  }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible' && !extensionInstalled.value) {
    checkExtension()
  }
}

function configureExtension() {
  const token = localStorage.getItem('token')
  const serverUrl = window.location.origin
  window.postMessage({
    type: 'INTENT_MONEY_SET_CONFIG',
    payload: { serverUrl, authToken: token || '' }
  }, '*')
}

async function extensionLogin(platformKey: string) {
  return new Promise<void>((resolve, reject) => {
    const requestId = `ext_${Date.now()}`
    const timeout = setTimeout(() => {
      window.removeEventListener('message', handler)
      reject(new Error('扩展通信超时'))
    }, 10000)

    function handler(event: MessageEvent) {
      if (event.data?.type === 'INTENT_MONEY_COOKIES_RESULT' && event.data?.requestId === requestId) {
        clearTimeout(timeout)
        window.removeEventListener('message', handler)
        if (event.data.success && event.data.cookies) {
          extensionCookieLogin(platformKey, event.data.cookies)
            .then(() => resolve())
            .catch((err) => reject(err))
        } else {
          reject(new Error(event.data.error || '获取Cookie失败'))
        }
      }
    }

    window.addEventListener('message', handler)
    window.postMessage({
      type: 'INTENT_MONEY_GET_COOKIES',
      requestId,
      payload: { platform: platformKey === 'xhs' ? 'xiaohongshu' : platformKey }
    }, '*')
  })
}

async function extensionGuidedLogin(platformKey: string) {
  const platformName = platformKey === 'xhs' ? 'xiaohongshu' : platformKey

  window.postMessage({
    type: 'INTENT_MONEY_OPEN_LOGIN',
    payload: { platform: platformName }
  }, '*')

  showToast('已打开登录页面，请在新标签页中完成登录')

  return new Promise<void>((resolve, reject) => {
    const requestId = `guided_${Date.now()}`
    const timeout = setTimeout(() => {
      window.removeEventListener('message', handler)
      reject(new Error('登录超时'))
    }, 120000)

    function handler(event: MessageEvent) {
      if (event.data?.type === 'INTENT_MONEY_COOKIES_RESULT' && event.data?.requestId === requestId) {
        clearTimeout(timeout)
        window.removeEventListener('message', handler)
        if (event.data.success && event.data.cookies) {
          extensionCookieLogin(platformKey, event.data.cookies)
            .then(() => resolve())
            .catch((err) => reject(err))
        } else {
          reject(new Error(event.data.error || '获取Cookie失败'))
        }
      }
    }

    window.addEventListener('message', handler)
  })
}

async function handleFetchCookies(platformKey: string) {
  try {
    await extensionLogin(platformKey)
    showToast('Cookie获取成功')
    await fetchAccounts()
  } catch (e: any) {
    showToast(e.message || '获取Cookie失败')
  }
}

async function extensionTriggerPopup(platformKey: string) {
  return new Promise<void>((resolve, reject) => {
    const requestId = `popup_${Date.now()}`
    const timeout = setTimeout(() => {
      window.removeEventListener('message', handler)
      reject(new Error('调起扩展超时'))
    }, 5000)

    function handler(event: MessageEvent) {
      if (event.data?.type === 'INTENT_MONEY_TRIGGER_POPUP_RESULT' && event.data?.requestId === requestId) {
        clearTimeout(timeout)
        window.removeEventListener('message', handler)
        if (event.data.success) {
          resolve()
        } else {
          reject(new Error(event.data.error || '调起扩展失败'))
        }
      }
    }

    window.addEventListener('message', handler)
    window.postMessage({
      type: 'INTENT_MONEY_TRIGGER_POPUP',
      requestId,
      payload: { platform: platformKey === 'xhs' ? 'xiaohongshu' : platformKey }
    }, '*')
  })
}

async function handleOneClickLogin(platformKey: string) {
  if (!extensionInstalled.value) {
    startQrLogin(platformKey)
    return
  }

  if (extensionStatus[platformKey]?.loggedIn) {
    try {
      await extensionLogin(platformKey)
      showToast('登录成功')
      await fetchAccounts()
    } catch (e: any) {
      showToast(e.message || '同步失败')
    }
    return
  }

  try {
    await extensionTriggerPopup(platformKey)
    showToast('已调起扩展，请在扩展中完成登录')
  } catch {
    try {
      await extensionGuidedLogin(platformKey)
      showToast('登录成功')
      await fetchAccounts()
    } catch (guidedErr: any) {
      showToast(guidedErr.message || '扩展登录失败')
    }
  }
}

async function startQrLogin(platformKey: string) {
  if (extensionInstalled.value) {
    try {
      await extensionLogin(platformKey)
      showToast('登录成功')
      await fetchAccounts()
      return
    } catch {
      try {
        await extensionGuidedLogin(platformKey)
        showToast('登录成功')
        await fetchAccounts()
        return
      } catch (guidedErr: any) {
        showToast(guidedErr.message || '扩展登录失败')
        return
      }
    }
  }

  qrPlatform.value = platformKey
  qrCodeUrl.value = ''
  qrStatus.value = ''
  qrLoading.value = true
  qrDialogVisible.value = true

  try {
    const res = await requestQrCode(platformKey)
    qrSessionId.value = res.data.login_session_id
    qrCodeUrl.value = res.data.qr_code_url
    qrLoading.value = false
    startQrPoll()
  } catch (e: any) {
    qrLoading.value = false
    const msg = e?.response?.data?.detail || '启动扫码登录失败'
    showToast(msg)
    qrDialogVisible.value = false
  }
}

function startQrPoll() {
  stopQrPoll()
  qrPollTimer = setInterval(async () => {
    try {
      const res = await checkQrCodeStatus(qrPlatform.value, qrSessionId.value)
      qrStatus.value = res.data.status
      if (res.data.status === 'confirmed') {
        stopQrPoll()
        showToast('登录成功')
        await fetchAccounts()
        setTimeout(() => {
          qrDialogVisible.value = false
        }, 1500)
      } else if (res.data.status === 'expired' || res.data.status === 'failed') {
        stopQrPoll()
      }
    } catch {
      stopQrPoll()
    }
  }, 2000)
}

function stopQrPoll() {
  if (qrPollTimer) {
    clearInterval(qrPollTimer)
    qrPollTimer = null
  }
}

function retryQrLogin() {
  startQrLogin(qrPlatform.value)
}

async function handleValidate(platformKey: string) {
  try {
    const res = await validateAccount(platformKey)
    const valid = res.data.valid
    showToast(valid ? 'Cookie有效' : 'Cookie已过期，请重新绑定')
    await fetchAccounts()
  } catch {
    showToast('验证失败，但Cookie已保存，可尝试重新验证或重新获取')
  }
}

async function handleUnbind(platformKey: string) {
  const platformName = platforms.find(p => p.key === platformKey)?.name || platformKey
  try {
    await showConfirmDialog({ title: '确认解绑', message: `确定要解绑${platformName}账号吗？` })
    await unbindAccount(platformKey)
    showToast('已解绑')
    await fetchAccounts()
  } catch {
  }
}
</script>

<style scoped>
.account-page {
  min-height: 100vh;
  background: var(--ink-black);
}

.account-content {
  padding: 16px var(--page-padding) 40px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-gray);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.login-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 245, 212, 0.06);
  border: 1px solid rgba(0, 245, 212, 0.15);
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 12px;
  color: var(--ink-gray);
  line-height: 1.5;
}

.login-hint code {
  background: rgba(0, 245, 212, 0.12);
  color: var(--neon-cyan);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
}

.login-hint.extension-connected {
  background: rgba(0, 245, 212, 0.08);
  border-color: rgba(0, 245, 212, 0.25);
}

.login-hint.extension-missing {
  background: rgba(255, 214, 10, 0.06);
  border-color: rgba(255, 214, 10, 0.15);
}

.account-card {
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 20px 16px;
  margin-bottom: 14px;
  transition: border-color 0.3s ease;
}

.account-card.card-bound {
  border-color: rgba(0, 245, 212, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.platform-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.platform-info {
  flex: 1;
}

.platform-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 4px;
}

.platform-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.status-active {
  background: var(--neon-cyan);
  box-shadow: 0 0 6px var(--neon-cyan);
}

.status-dot.status-expired {
  background: var(--neon-magenta);
  box-shadow: 0 0 6px var(--neon-magenta);
}

.status-dot.status-pending {
  background: #ffd60a;
}

.status-dot.status-unbound {
  background: var(--ink-gray);
}

.status-text {
  font-size: 13px;
  color: var(--ink-gray);
}

.ext-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  background: rgba(0, 245, 212, 0.15);
  color: var(--neon-cyan);
  font-size: 11px;
  border-radius: 4px;
  margin-left: 4px;
  font-weight: 500;
}

.card-detail {
  margin-bottom: 14px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.detail-label {
  font-size: 12px;
  color: var(--ink-gray);
}

.detail-value {
  font-size: 12px;
  color: var(--paper-dim);
}

.text-warning {
  color: #ffd60a;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-action {
  padding: 8px 14px;
  border-radius: var(--radius-button);
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--neon-cyan);
  color: var(--ink-black);
}

.btn-primary:hover {
  box-shadow: 0 0 12px rgba(0, 245, 212, 0.4);
}

.btn-secondary {
  background: rgba(0, 245, 212, 0.1);
  color: var(--neon-cyan);
  border: 1px solid rgba(0, 245, 212, 0.3);
}

.btn-outline {
  background: transparent;
  color: var(--ink-gray);
  border: 1px solid var(--border-gray);
}

.btn-danger {
  background: transparent;
  color: var(--neon-magenta);
  border: 1px solid rgba(255, 0, 110, 0.3);
}

.btn-action:active {
  transform: scale(0.96);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--ink-gray);
}

.empty-hint {
  font-size: 13px;
  margin-top: 8px;
  opacity: 0.6;
}

.dialog-content {
  padding: 16px;
}

.dialog-field {
  margin-bottom: 16px;
}

.dialog-field label {
  display: block;
  font-size: 13px;
  color: var(--ink-gray);
  margin-bottom: 8px;
}

.qr-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 8px;
}

.qr-loading {
  padding: 40px;
}

.qr-image-wrapper {
  text-align: center;
  width: 100%;
}

.qr-image {
  width: 100%;
  height: auto;
  max-height: 75vh;
  border-radius: 8px;
  border: 1px solid var(--border-gray);
  object-fit: contain;
}

.qr-tip {
  margin-top: 12px;
  font-size: 13px;
  color: var(--ink-gray);
}

.qr-success, .qr-expired {
  text-align: center;
  padding: 20px;
}

.qr-success p, .qr-expired p {
  margin-top: 12px;
  color: var(--paper-white);
}
</style>
