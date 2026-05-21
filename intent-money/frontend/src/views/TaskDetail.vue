<template>
  <div class="task-page">
    <div class="custom-nav">
      <div class="nav-back" @click="router.back()">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="nav-title">今日任务</div>
      <div class="nav-action" @click="router.push('/history')">
        <van-icon name="clock-o" size="20" />
      </div>
    </div>

    <div v-if="task" class="task-content">
      <div class="task-header">
        <div class="platform-tags">
          <span class="tag tag-primary">{{ task.platform_name }}</span>
          <span v-if="task.is_optimized" class="tag tag-success">已优化</span>
        </div>
      </div>

      <div v-if="task.is_optimized" class="info-banner banner-pink">
        <van-icon name="info-o" class="banner-icon" />
        <span>这条内容已针对上次问题优化</span>
      </div>

      <div class="info-banner banner-blue">
        <van-icon name="bulb-o" class="banner-icon" />
        <span>{{ task.why_it_works }}</span>
      </div>

      <div class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: var(--xh-brand)"></div>
          <h3 class="card-title">3秒钩子</h3>
          <button class="copy-btn" @click="copyText(task.hook_text)">复制</button>
        </div>
        <div class="hook-content">"{{ task.hook_text }}"</div>
      </div>

      <div class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #8b5cf6"></div>
          <h3 class="card-title">分镜脚本</h3>
        </div>
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

      <div class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #06b6d4"></div>
          <h3 class="card-title">口播文案</h3>
          <button class="copy-btn" @click="copyText(task.script_text)">复制</button>
        </div>
        <div class="script-content">{{ task.script_text }}</div>
      </div>

      <div class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #f59e0b"></div>
          <h3 class="card-title">发布标题</h3>
          <button class="copy-btn" @click="copyText(task.title)">复制</button>
        </div>
        <div class="title-content">{{ task.title }}</div>
      </div>

      <div class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #10b981"></div>
          <h3 class="card-title">评论区话术</h3>
          <button class="copy-btn" @click="copyText(task.comment_template)">复制</button>
        </div>
        <div class="comment-content">{{ task.comment_template }}</div>
      </div>

      <div v-if="task.intent_name === '成交赚钱' && dealScripts.length" class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #10b981"></div>
          <h3 class="card-title">促单话术</h3>
        </div>
        <div v-for="(item, idx) in dealScripts" :key="idx" class="conversion-script-item">
          <div class="script-stage-title">{{ item.title }}</div>
          <div class="script-stage-content" style="border-left: 3px solid #10b981">{{ formatScripts(item.scripts) }}</div>
        </div>
      </div>

      <div v-if="task.intent_name === '裂变招募分销' && recruitScripts.length" class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #4A90D9"></div>
          <h3 class="card-title">招募话术</h3>
        </div>
        <div v-for="(item, idx) in recruitScripts" :key="idx" class="conversion-script-item">
          <div class="script-stage-title">{{ item.title }}</div>
          <div class="script-stage-content" style="border-left: 3px solid #4A90D9">{{ formatScripts(item.scripts) }}</div>
        </div>
      </div>

      <div v-if="task.intent_name === 'IP长期增长' && ipScripts.length" class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: #8B5CF6"></div>
          <h3 class="card-title">粉丝运营话术</h3>
        </div>
        <div v-for="(item, idx) in ipScripts" :key="idx" class="conversion-script-item">
          <div class="script-stage-title">{{ item.title }}</div>
          <div class="script-stage-content" style="border-left: 3px solid #8B5CF6">{{ formatScripts(item.scripts) }}</div>
        </div>
      </div>

      <div v-if="task.is_optimized && task.optimization_note" class="task-card">
        <div class="card-header">
          <div class="card-bar" style="background: var(--xh-warning)"></div>
          <h3 class="card-title">优化说明</h3>
        </div>
        <div class="optimization-content">{{ task.optimization_note }}</div>
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
        color="var(--xh-brand)"
        @click="handlePublish"
      >
        我已发布
      </van-button>
      <div v-else-if="task?.status === 'PUBLISHED'" class="published-status">
        <van-icon name="checked" color="var(--xh-success)" size="20" />
        <span>已发布，等待数据回填</span>
      </div>
      <van-button
        v-if="task?.status === 'PUBLISHED'"
        type="success"
        block
        round
        size="large"
        color="var(--xh-success)"
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
        color="var(--xh-brand)"
        @click="handleSwap"
      >
        换一条
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { getCurrentTask, publishTask, swapTask } from '../api/tasks'

interface StoryboardShot {
  shot: number
  description: string
  duration: string
}

interface ConversionScriptItem {
  title: string
  scripts: Record<string, string> | string
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
  intent_name?: string
  conversion_scripts?: Record<string, ConversionScriptItem[]> | null
}

const route = useRoute()
const router = useRouter()
const task = ref<Task | null>(null)

const dealScripts = computed<ConversionScriptItem[]>(() => {
  if (!task.value?.conversion_scripts) return []
  const cs = task.value.conversion_scripts
  return [...(cs.private_to_deal || []), ...(cs.deal_boost || [])]
})

const recruitScripts = computed<ConversionScriptItem[]>(() => {
  if (!task.value?.conversion_scripts) return []
  const cs = task.value.conversion_scripts
  return [...(cs.public_to_private || []), ...(cs.private_to_deal || [])]
})

const ipScripts = computed<ConversionScriptItem[]>(() => {
  if (!task.value?.conversion_scripts) return []
  return task.value.conversion_scripts.public_to_private || []
})

const formatScripts = (scripts: Record<string, string> | string): string => {
  if (typeof scripts === 'string') return scripts
  return Object.entries(scripts)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n')
}

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
  background: var(--xh-bg-secondary);
  display: flex;
  flex-direction: column;
  padding-bottom: 160px;
}

.custom-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 12px;
  background: var(--xh-bg-primary);
  border-bottom: 1px solid var(--xh-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-back {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--xh-text-primary);
}

.nav-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--xh-text-primary);
}

.nav-action {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--xh-text-secondary);
}

.task-content {
  flex: 1;
  padding: 16px;
}

.task-header {
  margin-bottom: 12px;
}

.platform-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--radius-tag);
  font-size: 12px;
  font-weight: 500;
}

.tag-primary {
  background: var(--xh-brand-light);
  color: var(--xh-brand);
}

.tag-success {
  background: #ecfdf5;
  color: var(--xh-success);
}

.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  border-radius: var(--radius-card);
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.banner-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.banner-pink {
  background: var(--xh-brand-light);
  color: var(--xh-brand);
}

.banner-blue {
  background: #f0f9ff;
  color: #0369a1;
}

.task-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.card-bar {
  width: 4px;
  height: 18px;
  border-radius: 2px;
  flex-shrink: 0;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--xh-text-primary);
  margin: 0;
  flex: 1;
}

.copy-btn {
  background: none;
  border: 1px solid var(--xh-border);
  border-radius: var(--radius-tag);
  padding: 4px 12px;
  font-size: 12px;
  color: var(--xh-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.copy-btn:hover {
  border-color: var(--xh-brand);
  color: var(--xh-brand);
}

.copy-btn:active {
  transform: scale(0.95);
}

.hook-content {
  font-size: 18px;
  font-weight: 600;
  color: var(--xh-brand);
  line-height: 1.6;
  padding: 8px 0;
}

.script-content {
  font-size: 14px;
  color: var(--xh-text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.title-content {
  font-size: 15px;
  color: #0369a1;
  font-weight: 500;
  line-height: 1.5;
}

.comment-content {
  background: var(--xh-bg-secondary);
  padding: 14px;
  border-radius: var(--radius-input);
  font-size: 14px;
  color: var(--xh-text-secondary);
  line-height: 1.6;
  border-left: 3px solid var(--xh-success);
}

.optimization-content {
  background: #fef3c7;
  padding: 14px;
  border-radius: var(--radius-input);
  font-size: 14px;
  color: var(--xh-text-secondary);
  line-height: 1.6;
  border-left: 3px solid var(--xh-warning);
}

.storyboard {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  background: linear-gradient(135deg, #667eea 0%, #8b5cf6 100%);
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
  color: var(--xh-text-primary);
  line-height: 1.5;
}

.shot-duration {
  font-size: 12px;
  color: var(--xh-text-tertiary);
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
  background: var(--xh-bg-primary);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
}

.published-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: var(--xh-success);
  font-size: 15px;
}

.conversion-script-item {
  margin-bottom: 12px;
}

.conversion-script-item:last-child {
  margin-bottom: 0;
}

.script-stage-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--xh-text-primary);
  margin-bottom: 6px;
}

.script-stage-content {
  background: var(--xh-bg-secondary);
  padding: 14px;
  border-radius: var(--radius-input);
  font-size: 14px;
  color: var(--xh-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
