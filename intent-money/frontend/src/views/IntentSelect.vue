<template>
  <div class="intent-page">
    <div class="intent-header">
      <h1 class="intent-title">
        <span class="title-line">今天你想通过</span>
        <span class="title-line">什么方式赚钱？</span>
      </h1>
      <p class="intent-subtitle">
        <span class="typing-text">选一个赚钱目标，AI 替你搞定一切</span>
      </p>
    </div>

    <div class="intent-grid">
      <div
        v-for="(intent, index) in intents"
        :key="intent.id"
        class="intent-card"
        :style="{
          animationDelay: `${index * 100 + 200}ms`,
          '--intent-color': getIntentColor(intent.sort_order),
          '--intent-glow': getIntentGlow(intent.sort_order),
        }"
        @click="selectIntent(intent)"
      >
        <div class="intent-glow-border"></div>
        <div class="intent-icon">
          <svg viewBox="0 0 48 48" fill="none" :stroke="getIntentColor(intent.sort_order)" stroke-width="1.5">
            <template v-if="intent.sort_order === 1">
              <circle cx="24" cy="24" r="18" stroke-linecap="round" stroke-dasharray="4 4"/>
              <circle cx="24" cy="24" r="8" fill="currentColor" fill-opacity="0.2"/>
              <path d="M24 10v6M24 32v6M10 24h6M32 24h6"/>
            </template>
            <template v-else-if="intent.sort_order === 2">
              <rect x="8" y="14" width="32" height="20" rx="4" stroke-linecap="round"/>
              <path d="M16 22h4M16 26h8" stroke-linecap="round"/>
              <circle cx="34" cy="24" r="3" fill="currentColor" fill-opacity="0.3"/>
            </template>
            <template v-else-if="intent.sort_order === 3">
              <circle cx="16" cy="24" r="6" stroke-linecap="round"/>
              <circle cx="32" cy="24" r="6" stroke-linecap="round"/>
              <path d="M22 24h4" stroke-linecap="round" stroke-dasharray="2 2"/>
            </template>
            <template v-else>
              <path d="M24 6v6M24 36v6M6 24h6M36 24h6" stroke-linecap="round"/>
              <circle cx="24" cy="24" r="10" stroke-linecap="round"/>
              <path d="M24 18v6l4 4" stroke-linecap="round" stroke-linejoin="round"/>
            </template>
          </svg>
        </div>
        <div class="intent-name">{{ intent.name }}</div>
        <div class="intent-desc">{{ intent.description }}</div>
        <div class="intent-arrow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" :stroke="getIntentColor(intent.sort_order)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </div>
      </div>
    </div>

    <div class="intent-footer">
      <div class="history-link" @click="router.push('/history')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        <span>查看历史任务</span>
      </div>
      <div class="admin-link" @click="router.push('/admin')">运营后台</div>
    </div>

    <!-- Feedback Overlay -->
    <Transition name="overlay-fade">
      <div v-if="showFeedback" class="feedback-overlay" @click.self="dismissFeedback">
        <div class="feedback-card">
          <div class="feedback-pulse"></div>
          <div class="feedback-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="20" stroke="var(--neon-cyan)" stroke-width="1.5" stroke-dasharray="4 4">
                <animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="8s" repeatCount="indefinite"/>
              </circle>
              <circle cx="24" cy="24" r="12" fill="var(--neon-cyan)" fill-opacity="0.1" stroke="var(--neon-cyan)" stroke-width="1"/>
              <path d="M20 24l3 3 6-6" stroke="var(--neon-cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="feedback-text">AI 正在基于实时爆款数据<br>为你生成最优赚钱方案</div>
          <div class="feedback-dots">
            <span class="dot" style="animation-delay: 0s"></span>
            <span class="dot" style="animation-delay: 0.2s"></span>
            <span class="dot" style="animation-delay: 0.4s"></span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getIntents } from '../api/tasks'
import { track } from '../utils/tracker'

interface Intent {
  id: string
  name: string
  description: string
  is_active: boolean
  sort_order: number
}

const router = useRouter()
const intents = ref<Intent[]>([])
const loading = ref(false)
const showFeedback = ref(false)
const selectedIntentId = ref('')

const getIntentColor = (sortOrder: number): string => {
  const colorMap: Record<number, string> = {
    1: '#00f5d4',
    2: '#ff006e',
    3: '#ffd60a',
    4: '#9b5de5',
  }
  return colorMap[sortOrder] || '#00f5d4'
}

const getIntentGlow = (sortOrder: number): string => {
  const glowMap: Record<number, string> = {
    1: 'rgba(0, 245, 212, 0.3)',
    2: 'rgba(255, 0, 110, 0.3)',
    3: 'rgba(255, 214, 10, 0.3)',
    4: 'rgba(155, 93, 229, 0.3)',
  }
  return glowMap[sortOrder] || 'rgba(0, 245, 212, 0.3)'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getIntents()
    intents.value = res.data.intents || res.data
  } catch (e) {
    showToast('加载失败，请重试')
  } finally {
    loading.value = false
  }
})

const selectIntent = (intent: Intent) => {
  track('intent_selected', { page: '/', metadata: { intent_id: intent.id, intent_name: intent.name } })
  selectedIntentId.value = intent.id
  showFeedback.value = true
  setTimeout(() => {
    showFeedback.value = false
    router.push(`/platform/${intent.id}`)
  }, 1800)
}

const dismissFeedback = () => {
  showFeedback.value = false
  if (selectedIntentId.value) {
    router.push(`/platform/${selectedIntentId.value}`)
  }
}
</script>

<style scoped>
.intent-page {
  min-height: 100vh;
  position: relative;
  z-index: 1;
  padding: 48px var(--page-padding) 40px;
  display: flex;
  flex-direction: column;
}

/* Header */
.intent-header {
  margin-bottom: 40px;
  animation: fadeInUp 0.6s ease-out forwards;
}

.intent-title {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--paper-white);
  margin: 0 0 16px;
  line-height: 1.3;
  letter-spacing: -0.5px;
}

.title-line {
  display: block;
}

.title-line:last-child {
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.intent-subtitle {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-gray);
  margin: 0;
  letter-spacing: 0.5px;
}

.typing-text {
  border-right: 2px solid var(--neon-cyan);
  animation: blink 1s step-end infinite;
  padding-right: 4px;
}

/* Grid */
.intent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  flex: 1;
}

/* Card */
.intent-card {
  position: relative;
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 28px 16px 20px;
  text-align: center;
  cursor: pointer;
  opacity: 0;
  transform: translateY(20px);
  animation: cardEnter 0.5s ease forwards;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

@keyframes cardEnter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.intent-glow-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--intent-color);
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.intent-card:hover {
  transform: translateY(-3px);
  border-color: var(--intent-color);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px var(--intent-glow);
}

.intent-card:hover .intent-glow-border {
  opacity: 1;
  box-shadow: 0 0 12px var(--intent-glow);
}

.intent-card:active {
  transform: scale(0.97);
}

.intent-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 14px;
}

.intent-icon svg {
  width: 100%;
  height: 100%;
}

.intent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 8px;
}

.intent-desc {
  font-size: 12px;
  color: var(--ink-gray);
  line-height: 1.5;
  margin-bottom: 12px;
}

.intent-arrow {
  opacity: 0;
  transform: translateX(-4px);
  transition: all 0.3s ease;
}

.intent-card:hover .intent-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* Footer */
.intent-footer {
  margin-top: 32px;
  text-align: center;
}

.history-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  color: var(--ink-gray);
  font-size: 14px;
  cursor: pointer;
  border-radius: var(--radius-button);
  transition: all 0.2s ease;
}

.history-link:hover {
  color: var(--neon-cyan);
  background: rgba(0, 245, 212, 0.08);
}

.history-link svg {
  transition: transform 0.3s ease;
}

.history-link:hover svg {
  transform: rotate(30deg);
}

.admin-link {
  margin-top: 12px;
  padding: 6px;
  color: var(--ink-gray);
  font-size: 12px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.admin-link:hover {
  opacity: 1;
  color: var(--paper-dim);
}

/* Feedback Overlay */
.feedback-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 32px;
}

.feedback-card {
  position: relative;
  background: var(--gradient-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-card);
  padding: 40px 32px;
  text-align: center;
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
  max-width: 320px;
  width: 100%;
  overflow: hidden;
}

.feedback-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100px;
  height: 100px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: var(--neon-cyan-dim);
  animation: pulseRing 2s ease-out infinite;
}

@keyframes pulseRing {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0.6;
  }
  100% {
    transform: translate(-50%, -50%) scale(2.5);
    opacity: 0;
  }
}

.feedback-icon {
  position: relative;
  z-index: 2;
  margin-bottom: 20px;
}

.feedback-text {
  position: relative;
  z-index: 2;
  font-size: 15px;
  font-weight: 500;
  color: var(--paper-white);
  line-height: 1.7;
  margin-bottom: 20px;
}

.feedback-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--neon-cyan);
  animation: dotPulse 1.4s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.3s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}
</style>
