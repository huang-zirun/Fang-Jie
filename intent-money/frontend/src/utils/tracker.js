const STORAGE_KEY = 'im_session_id'
const FLUSH_INTERVAL = 5000
const MAX_BATCH_SIZE = 20

let buffer = []
let timer = null
let pageEnterTime = 0
let currentPage = ''

function getSessionId() {
  let id = localStorage.getItem(STORAGE_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(STORAGE_KEY, id)
  }
  return id
}

function flush(useBeaconOnly = false) {
  if (buffer.length === 0) return
  const payload = {
    session_id: getSessionId(),
    events: buffer.slice(0, MAX_BATCH_SIZE),
  }
  buffer = buffer.slice(payload.events.length)
  const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/events', blob)
    return
  }
  
  if (useBeaconOnly) return
  
  fetch('/api/v1/events', { method: 'POST', body: JSON.stringify(payload), headers, keepalive: true }).catch(() => {})
}

function startTimer() {
  if (timer) return
  timer = setInterval(flush, FLUSH_INTERVAL)
}

export function track(eventType, { page, duration, metadata } = {}) {
  buffer.push({
    event_type: eventType,
    page: page || currentPage || location.pathname,
    duration: duration ?? null,
    metadata_json: metadata ?? null,
  })
  if (buffer.length >= MAX_BATCH_SIZE) {
    flush()
  }
}

export function trackPageView(page) {
  const now = Date.now()
  if (pageEnterTime && currentPage) {
    const elapsed = (now - pageEnterTime) / 1000
    track('page_view', { page: currentPage, duration: Math.round(elapsed * 100) / 100 })
  }
  currentPage = page || location.pathname
  pageEnterTime = now
}

export function initTracker() {
  getSessionId()
  startTimer()
  trackPageView(location.pathname)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      flush()
    }
  })
  window.addEventListener('beforeunload', () => {
    flush(true)
  })
}
