<template>
  <div class="platform-page">
    <van-nav-bar
      title="选择平台"
      left-arrow
      @click-left="router.back()"
    />
    <div class="platform-header">
      <h1 class="platform-title">在哪个平台发布？</h1>
      <p class="platform-subtitle">选择你的发布平台，系统将为你匹配最优内容结构</p>
    </div>
    <div class="platform-grid">
      <div
        v-for="platform in platforms"
        :key="platform.id"
        class="platform-card"
        @click="selectPlatform(platform)"
      >
        <div class="platform-icon">{{ platform.icon }}</div>
        <div class="platform-name">{{ platform.name }}</div>
        <div class="platform-desc">{{ platform.description }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getPlatforms, createTask, getCurrentTask } from '../api/tasks'

interface Platform {
  id: string
  name: string
  icon: string
  description: string
}

const router = useRouter()
const route = useRoute()
const intentId = route.params.intentId as string
const platforms = ref<Platform[]>([])

onMounted(async () => {
  try {
    const res = await getPlatforms()
    const list = res.data.platforms || res.data
    const iconMap: Record<string, string> = {
      douyin: '🎵',
      xiaohongshu: '📕',
    }
    platforms.value = (list || []).map((p: any) => ({
      id: p.id,
      name: p.name,
      icon: iconMap[p.code] || '📱',
      description: p.description,
    }))
  } catch {
    showToast('加载平台失败')
  }
})

const selectPlatform = async (platform: Platform) => {
  const toast = showLoadingToast({ message: '生成任务中...', forbidClick: true, duration: 0 })
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
        const taskRes = await getCurrentTask()
        const existingTask = taskRes.data.task || taskRes.data
        router.push(`/task/${existingTask.id}`)
      } catch {
        showToast('你已有未完成的任务')
      }
    } else {
      showToast('生成失败，请重试')
    }
  } finally {
    closeToast()
  }
}
</script>

<style scoped>
.platform-page {
  min-height: 100vh;
  background: var(--xh-bg-primary);
}

.platform-header {
  padding: 24px 16px 32px;
}

.platform-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--xh-text-primary);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.platform-subtitle {
  font-size: 14px;
  color: var(--xh-text-tertiary);
  margin: 0;
}

.platform-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 0 16px;
}

.platform-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 28px 16px 20px;
  text-align: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--xh-border);
  cursor: pointer;
}

.platform-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-float);
}

.platform-card:active {
  transform: scale(0.97);
}

.platform-icon {
  font-size: 40px;
  margin-bottom: 12px;
  line-height: 1;
}

.platform-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--xh-text-primary);
  margin-bottom: 6px;
}

.platform-desc {
  font-size: 12px;
  color: var(--xh-text-tertiary);
  line-height: 1.4;
}
</style>
