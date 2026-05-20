<template>
  <div class="task-page">
    <van-nav-bar title="今日任务" left-arrow @click-left="router.back()" />

    <div v-if="task" class="task-content">
      <div class="task-header">
        <div class="platform-tag">
          <van-tag type="primary" size="medium">{{ task.platform_name }}</van-tag>
          <van-tag v-if="task.is_optimized" type="success" size="medium" style="margin-left: 8px">
            已优化
          </van-tag>
        </div>
      </div>

      <div v-if="task.is_optimized" class="optimization-banner">
        <van-notice-bar
          text="🔧 这条内容已针对上次问题优化"
          background="#ecfdf5"
          color="#059669"
          left-icon="info-o"
        />
      </div>

      <div class="why-it-works">
        <van-notice-bar :text="`💡 ${task.why_it_works}`" background="#f0f9ff" color="#0369a1" />
      </div>

      <div class="task-section">
        <div class="section-header">
          <h3 class="section-title">🎬 3秒钩子</h3>
          <van-button size="mini" plain @click="copyText(task.hook_text)">复制</van-button>
        </div>
        <div class="section-content hook-text">{{ task.hook_text }}</div>
      </div>

      <div class="task-section">
        <h3 class="section-title">📷 分镜脚本</h3>
        <div class="storyboard">
          <div v-for="shot in task.storyboard" :key="shot.shot" class="shot-item">
            <div class="shot-number">{{ shot.shot }}</div>
            <div class="shot-info">
              <div class="shot-desc">{{ shot.description }}</div>
              <div class="shot-duration">{{ shot.duration }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="task-section">
        <div class="section-header">
          <h3 class="section-title">📝 口播文案</h3>
          <van-button size="mini" plain @click="copyText(task.script_text)">复制</van-button>
        </div>
        <div class="section-content script-text">{{ task.script_text }}</div>
      </div>

      <div class="task-section">
        <div class="section-header">
          <h3 class="section-title">🏷️ 发布标题</h3>
          <van-button size="mini" plain @click="copyText(task.title)">复制</van-button>
        </div>
        <div class="section-content title-text">{{ task.title }}</div>
      </div>

      <div class="task-section">
        <div class="section-header">
          <h3 class="section-title">💬 评论区话术</h3>
          <van-button size="mini" plain @click="copyText(task.comment_template)">复制</van-button>
        </div>
        <div class="section-content comment-text">{{ task.comment_template }}</div>
      </div>

      <div v-if="task.is_optimized && task.optimization_note" class="task-section">
        <h3 class="section-title">🔧 优化说明</h3>
        <div class="section-content optimization-note">{{ task.optimization_note }}</div>
      </div>
    </div>

    <div v-else class="task-loading">
      <van-skeleton title :row="8" />
    </div>

    <div class="task-actions">
      <van-button
        v-if="task?.status === 'PENDING'"
        type="primary"
        block
        round
        size="large"
        @click="handlePublish"
      >
        我已发布
      </van-button>
      <div v-else-if="task?.status === 'PUBLISHED'" class="published-status">
        <van-icon name="checked" color="#07c160" size="20" />
        <span>已发布，等待数据回填</span>
      </div>
      <van-button
        v-if="task?.status === 'PUBLISHED'"
        type="success"
        block
        round
        size="large"
        style="margin-top: 8px"
        @click="router.push(`/report/${task.id}`)"
      >
        回填数据
      </van-button>
      <van-button
        v-if="task?.status === 'PENDING'"
        plain
        block
        round
        size="large"
        style="margin-top: 8px"
        @click="handleSwap"
      >
        换一条
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { getCurrentTask, publishTask, swapTask } from '../api/tasks'

interface StoryboardShot {
  shot: number
  description: string
  duration: string
}

interface Task {
  id: string
  platform_name: string
  hook_text: string
  storyboard: StoryboardShot[]
  script_text: string
  title: string
  comment_template: string
  why_it_works: string
  is_optimized: boolean
  optimization_note: string | null
  prev_task_id: string | null
  status?: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const task = ref<Task | null>(null)

onMounted(async () => {
  try {
    const res = await getCurrentTask()
    task.value = res.data.task || res.data
  } catch (e) {
    showToast('加载任务失败')
  }
})

const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast({ message: '已复制', icon: 'checked' })
  } catch {
    showToast('复制失败')
  }
}

const handlePublish = async () => {
  if (!task.value) return
  const toast = showLoadingToast({ message: '确认中...', forbidClick: true, duration: 0 })
  try {
    await publishTask(task.value.id)
    task.value.status = 'PUBLISHED'
    showToast({ message: '已确认发布', icon: 'checked' })
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showToast(detail || '操作失败')
  } finally {
    closeToast()
  }
}

const handleSwap = async () => {
  if (!task.value) return
  try {
    await showConfirmDialog({ title: '换一条', message: '今天只能换1次，确定要换吗？' })
  } catch {
    return
  }
  const toast = showLoadingToast({ message: '生成新任务...', forbidClick: true, duration: 0 })
  try {
    const res = await swapTask(task.value.id)
    task.value = res.data.task || res.data
    showToast({ message: '已换一条', icon: 'checked' })
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (e?.response?.status === 429) {
      showToast('今日换条次数已用')
    } else {
      showToast(detail || '换条失败')
    }
  } finally {
    closeToast()
  }
}
</script>

<style scoped>
.task-page {
  min-height: 100vh;
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
}

.task-content {
  flex: 1;
  padding: 16px;
  padding-bottom: 160px;
}

.task-header {
  margin-bottom: 12px;
}

.platform-tag {
  display: flex;
  align-items: center;
}

.optimization-banner {
  margin-bottom: 12px;
}

.why-it-works {
  margin-bottom: 16px;
}

.task-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header .section-title {
  margin-bottom: 0;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 10px;
}

.section-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.hook-text {
  font-size: 18px;
  font-weight: 600;
  color: #e74c3c;
}

.script-text {
  white-space: pre-wrap;
}

.title-text {
  color: #0369a1;
  font-weight: 500;
}

.comment-text {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #07c160;
}

.optimization-note {
  background: #fef3c7;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #f59e0b;
}

.storyboard {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.shot-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.shot-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #667eea;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.shot-info {
  flex: 1;
}

.shot-desc {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.shot-duration {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.task-loading {
  flex: 1;
  padding: 16px;
}

.task-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: #fff;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.08);
}

.published-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: #07c160;
  font-size: 15px;
}
</style>
