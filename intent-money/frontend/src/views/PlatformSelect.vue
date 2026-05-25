<template>
  <div class="platform-page">
    <CyberNav title="选择平台" />

    <div class="platform-content">
      <div class="platform-header">
        <h1 class="platform-title">在哪个平台发布？</h1>
        <p class="platform-subtitle">选择你的发布平台，系统将为你匹配最优内容结构</p>
      </div>

      <div class="platform-grid">
        <div
          v-for="platform in platforms"
          :key="platform.id"
          class="platform-card"
          :style="{ '--platform-color': getPlatformColor(platform.name) }"
          @click="selectPlatform(platform)"
        >
          <div class="platform-glow"></div>
          <div class="platform-icon">
            <PlatformIcon :platform="platform.name" :size="56" />
          </div>
          <div class="platform-name">{{ platform.name }}</div>
          <div class="platform-desc">{{ platform.description }}</div>
          <div class="platform-arrow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <Transition name="overlay-fade">
      <div v-if="generating" class="generating-overlay">
        <div class="generating-card">
          <div class="generating-spinner">
            <svg width="48" height="48" viewBox="0 0 48 48">
              <circle cx="24" cy="24" r="20" stroke="var(--border-gray)" stroke-width="3" fill="none"/>
              <circle cx="24" cy="24" r="20" stroke="var(--neon-cyan)" stroke-width="3" fill="none" stroke-dasharray="80 126" stroke-linecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="1s" repeatCount="indefinite"/>
              </circle>
            </svg>
          </div>
          <div class="generating-text">AI 正在匹配最优内容结构...</div>
          <div class="generating-sub">分析实时爆款数据 · 生成专属方案</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getPlatforms, createTask, getCurrentTask } from '../api/tasks'
import PlatformIcon from '../components/PlatformIcon.vue'
import CyberNav from '../components/CyberNav.vue'

interface Platform {
  id: string
  name: string
  description: string
}

const router = useRouter()
const route = useRoute()
const intentId = route.params.intentId as string
const platforms = ref<Platform[]>([])
const generating = ref(false)

const getPlatformColor = (name: string): string => {
  if (name === '抖音' || name === 'douyin') return '#ff006e'
  if (name === '小红书' || name === 'xiaohongshu') return '#00f5d4'
  return '#9b5de5'
}

onMounted(async () => {
  try {
    const res = await getPlatforms()
    const list = res.data.platforms || res.data
    platforms.value = (list || []).map((p: any) => ({
      id: p.id,
      name: p.name,
      description: p.description,
    }))
  } catch {
    showToast('加载平台失败')
  }
})

const selectPlatform = async (platform: Platform) => {
  generating.value = true
  try {
    const res = await createTask({
      intent_id: intentId,
      platform_id: platform.id,
      task_type: 'video',
    })
    const task = res.data.task || res.data
    router.push(`/task/${task.id}`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (detail === 'Has pending task') {
      try {
        const taskRes = await getCurrentTask(platform.id)
        const existingTask = taskRes.data.task || taskRes.data
        router.push(`/task/${existingTask.id}`)
      } catch {
        showToast('你已有未完成的任务')
      }
    } else {
      showToast('生成失败，请重试')
    }
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.platform-page {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.platform-content {
  padding: 24px var(--page-padding) 40px;
}

.platform-header {
  margin-bottom: 32px;
  animation: fadeInUp 0.5s ease-out forwards;
}

.platform-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--paper-white);
  margin: 0 0 10px;
  line-height: 1.3;
}

.platform-subtitle {
  font-size: 14px;
  color: var(--ink-gray);
  margin: 0;
  line-height: 1.5;
}

.platform-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}

.platform-card {
  position: relative;
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 32px 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.platform-glow {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--platform-color);
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.platform-card:hover {
  transform: translateX(4px);
  border-color: var(--platform-color);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px var(--platform-color);
}

.platform-card:hover .platform-glow {
  opacity: 1;
  box-shadow: 0 0 12px var(--platform-color);
}

.platform-card:active {
  transform: scale(0.98);
}

.platform-icon {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
}

.platform-icon img {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}

.platform-info {
  flex: 1;
}

.platform-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 6px;
}

.platform-desc {
  font-size: 13px;
  color: var(--ink-gray);
  line-height: 1.5;
}

.platform-arrow {
  color: var(--ink-gray);
  transition: all 0.3s ease;
}

.platform-card:hover .platform-arrow {
  color: var(--platform-color);
  transform: translateX(4px);
}

/* Generating Overlay */
.generating-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 10, 15, 0.9);
  backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 32px;
}

.generating-card {
  text-align: center;
}

.generating-spinner {
  margin-bottom: 24px;
}

.generating-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 8px;
}

.generating-sub {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-gray);
  letter-spacing: 0.5px;
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
