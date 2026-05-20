<template>
  <div class="intent-page">
    <div class="intent-header">
      <h1 class="intent-title">今天你想怎么赚钱？</h1>
      <p class="intent-subtitle">选择一个目标，系统给你今天要做的事</p>
    </div>
    <div class="intent-grid">
      <div
        v-for="intent in intents"
        :key="intent.id"
        class="intent-card"
        :class="{ active: intent.is_active, disabled: !intent.is_active }"
        @click="intent.is_active && selectIntent(intent)"
      >
        <div class="intent-icon">
          <span v-if="intent.sort_order === 1">🎯</span>
          <span v-else-if="intent.sort_order === 2">💰</span>
          <span v-else-if="intent.sort_order === 3">🔗</span>
          <span v-else>📈</span>
        </div>
        <div class="intent-name">{{ intent.name }}</div>
        <div class="intent-desc">{{ intent.description }}</div>
        <div v-if="!intent.is_active" class="intent-badge">即将开放</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getIntents, createTask } from '../api/tasks'

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

const selectIntent = async (intent: Intent) => {
  const toast = showLoadingToast({ message: '生成任务中...', forbidClick: true, duration: 0 })
  try {
    const DOUYIN_ID = '10000000-0000-0000-0000-000000000001'
    const res = await createTask({
      intent_id: intent.id,
      platform_id: DOUYIN_ID,
      task_type: 'video',
    })
    const task = res.data.task || res.data
    router.push(`/task/${task.id}`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (detail === 'Has pending task') {
      showToast('你已有未完成的任务')
    } else {
      showToast('生成失败，请重试')
    }
  } finally {
    closeToast()
  }
}
</script>

<style scoped>
.intent-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px 40px;
}

.intent-header {
  text-align: center;
  margin-bottom: 40px;
}

.intent-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 12px;
}

.intent-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.intent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.intent-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 24px 16px;
  text-align: center;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.intent-card.active {
  cursor: pointer;
}

.intent-card.active:active {
  transform: scale(0.97);
  background: rgba(255, 255, 255, 1);
}

.intent-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.intent-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.intent-name {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.intent-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}

.intent-badge {
  position: absolute;
  top: 8px;
  right: -20px;
  background: #eee;
  color: #999;
  font-size: 11px;
  padding: 2px 24px;
  transform: rotate(45deg);
}
</style>
