<template>
  <div class="intent-page">
    <div class="intent-header">
      <h1 class="intent-title">今天你想通过什么方式赚钱？</h1>
      <p class="intent-subtitle">选一个赚钱目标，系统帮你搞定一切</p>
    </div>
    <div class="intent-grid">
      <div
        v-for="(intent, index) in intents"
        :key="intent.id"
        class="intent-card"
        :style="{ animationDelay: `${index * 50}ms`, '--intent-color': getIntentColor(intent.sort_order) }"
        @click="selectIntent(intent)"
      >
        <div class="intent-stripe" :style="{ background: getIntentColor(intent.sort_order) }"></div>
        <div class="intent-icon" :style="{ color: getIntentColor(intent.sort_order) }">
          <span v-if="intent.sort_order === 1">🎯</span>
          <span v-else-if="intent.sort_order === 2">💰</span>
          <span v-else-if="intent.sort_order === 3">🔗</span>
          <span v-else>📈</span>
        </div>
        <div class="intent-name">{{ intent.name }}</div>
        <div class="intent-desc">{{ intent.description }}</div>
      </div>
    </div>
    <Transition name="overlay-fade">
      <div v-if="showFeedback" class="feedback-overlay" @click.self="dismissFeedback">
        <div class="feedback-card">
          <div class="feedback-icon">✨</div>
          <div class="feedback-text">我已基于当前平台+实时同类爆款数据，为你生成了今天最优赚钱动作方案</div>
        </div>
      </div>
    </Transition>

    <div class="history-entry" @click="router.push('/history')">
      <van-icon name="clock-o" size="16" />
      <span>查看历史任务</span>
    </div>

    <div class="admin-entry" @click="router.push('/admin')">管理后台</div>
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
    1: '#FF2442',
    2: '#FF8C00',
    3: '#4A90D9',
    4: '#8B5CF6',
  }
  return colorMap[sortOrder] || '#FF2442'
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
  }, 1500)
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
  background: var(--xh-bg-primary);
  padding: 48px 16px 40px;
}

.intent-header {
  margin-bottom: 32px;
}

.intent-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--xh-text-primary);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.intent-subtitle {
  font-size: 14px;
  color: var(--xh-text-tertiary);
  margin: 0;
}

.intent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.intent-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 28px 16px 20px;
  text-align: center;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--xh-border);
  cursor: pointer;
  opacity: 0;
  transform: translateY(16px);
  animation: cardEnter 0.4s ease forwards;
}

@keyframes cardEnter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.intent-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-float);
}

.intent-card:active {
  transform: scale(0.97);
}

.intent-stripe {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

.intent-icon {
  font-size: 40px;
  margin-bottom: 12px;
  line-height: 1;
}

.intent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--xh-text-primary);
  margin-bottom: 6px;
}

.intent-desc {
  font-size: 12px;
  color: var(--xh-text-tertiary);
  line-height: 1.4;
}

.feedback-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 32px;
}

.feedback-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 32px 24px;
  text-align: center;
  box-shadow: var(--shadow-float);
  max-width: 320px;
  width: 100%;
}

.feedback-icon {
  font-size: 48px;
  margin-bottom: 16px;
  line-height: 1;
}

.feedback-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--xh-text-primary);
  line-height: 1.6;
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.3s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.history-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 24px;
  padding: 12px;
  color: var(--xh-text-tertiary);
  font-size: 14px;
  cursor: pointer;
  transition: color 0.15s;
}

.history-entry:active {
  color: var(--xh-brand);
}

.admin-entry {
  text-align: center;
  margin-top: 16px;
  padding: 8px;
  color: #ccc;
  font-size: 12px;
  cursor: pointer;
}

.admin-entry:active {
  color: var(--xh-text-tertiary);
}
</style>
