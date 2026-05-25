<template>
  <div class="task-page">
    <CyberNav title="今日任务">
      <template #action>
        <div class="nav-action-btn" @click="router.push('/history')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
      </template>
    </CyberNav>

    <div v-if="task" class="task-content">
      <!-- Task Header -->
      <div class="task-header">
        <div class="platform-tags">
          <span class="tag tag-platform">{{ task.platform_name }}</span>
          <span v-if="task.is_optimized" class="tag tag-optimized">已优化</span>
        </div>
      </div>

      <!-- Info Banners -->
      <div v-if="task.is_optimized" class="info-banner banner-magenta">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span>这条内容已针对上次问题优化</span>
      </div>

      <div class="info-banner banner-cyan">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/>
          <path d="M9 21h6"/>
        </svg>
        <span>{{ task.why_it_works }}</span>
      </div>

      <!-- Hook Card -->
      <CyberCard variant="magenta" glow-border glow-color="magenta">
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-magenta)"></div>
          <h3 class="card-title">3秒钩子</h3>
          <button class="copy-btn" @click.stop="copyText(task.hook_text, 'hook_text')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            复制
          </button>
        </div>
        <div class="hook-content">"{{ task.hook_text }}"</div>
      </CyberCard>

      <!-- Storyboard Card -->
      <CyberCard>
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-purple)"></div>
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
      </CyberCard>

      <!-- Script Card -->
      <CyberCard>
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-cyan)"></div>
          <h3 class="card-title">口播文案</h3>
          <button class="copy-btn" @click.stop="copyText(task.script_text, 'script_text')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            复制
          </button>
        </div>
        <div class="script-content">{{ task.script_text }}</div>
      </CyberCard>

      <!-- Title Card -->
      <CyberCard>
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-gold)"></div>
          <h3 class="card-title">发布标题</h3>
          <button class="copy-btn" @click.stop="copyText(task.title, 'title')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            复制
          </button>
        </div>
        <div class="title-content">{{ task.title }}</div>
      </CyberCard>

      <!-- Comment Card -->
      <CyberCard>
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-gold)"></div>
          <h3 class="card-title">评论区话术</h3>
          <button class="copy-btn" @click.stop="copyText(task.comment_template, 'comment_template')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            复制
          </button>
        </div>
        <div class="comment-content">{{ task.comment_template }}</div>
      </CyberCard>

      <!-- Conversion Scripts -->
      <template v-if="task.intent_name === '成交赚钱' && dealScripts.length">
        <CyberCard variant="gold" glow-border glow-color="gold">
          <div class="card-header">
            <div class="card-bar" style="background: var(--neon-gold)"></div>
            <h3 class="card-title">促单话术</h3>
          </div>
          <div v-for="(item, idx) in dealScripts" :key="idx" class="conversion-item">
            <div class="conversion-stage">{{ item.title }}</div>
            <div class="conversion-text" style="border-left-color: var(--neon-gold)">{{ formatScripts(item.scripts) }}</div>
          </div>
        </CyberCard>
      </template>

      <template v-if="task.intent_name === '裂变招募分销' && recruitScripts.length">
        <CyberCard variant="cyan" glow-border glow-color="cyan">
          <div class="card-header">
            <div class="card-bar" style="background: var(--neon-cyan)"></div>
            <h3 class="card-title">招募话术</h3>
          </div>
          <div v-for="(item, idx) in recruitScripts" :key="idx" class="conversion-item">
            <div class="conversion-stage">{{ item.title }}</div>
            <div class="conversion-text" style="border-left-color: var(--neon-cyan)">{{ formatScripts(item.scripts) }}</div>
          </div>
        </CyberCard>
      </template>

      <template v-if="task.intent_name === 'IP长期增长' && ipScripts.length">
        <CyberCard variant="purple" glow-border glow-color="purple">
          <div class="card-header">
            <div class="card-bar" style="background: var(--neon-purple)"></div>
            <h3 class="card-title">粉丝运营话术</h3>
          </div>
          <div v-for="(item, idx) in ipScripts" :key="idx" class="conversion-item">
            <div class="conversion-stage">{{ item.title }}</div>
            <div class="conversion-text" style="border-left-color: var(--neon-purple)">{{ formatScripts(item.scripts) }}</div>
          </div>
        </CyberCard>
      </template>

      <!-- Optimization Note -->
      <CyberCard v-if="task.is_optimized && task.optimization_note" variant="gold">
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-gold)"></div>
          <h3 class="card-title">优化说明</h3>
        </div>
        <div class="optimization-content">{{ task.optimization_note }}</div>
      </CyberCard>
    </div>

    <!-- Loading State -->
    <div v-else class="task-loading">
      <van-skeleton title :row="8" />
    </div>

    <!-- Bottom Actions -->
    <div class="task-actions">
      <template v-if="task?.status === 'PENDING'">
        <CyberButton variant="primary" size="large" block :loading="publishState === 'confirming'" @click="handleManualConfirm">
          确认已发放
        </CyberButton>
        <div class="manual-publish-hint">复制话术并发到平台后，点这里进入数据回填</div>
        <div class="action-row">
          <CyberButton variant="secondary" size="default" :loading="publishState === 'publishing'" @click="handlePublish">
            自动发布
          </CyberButton>
          <CyberButton variant="ghost" size="default" @click="handleSwap">
            换一条
          </CyberButton>
        </div>
      </template>

      <template v-else-if="task?.status === 'PUBLISHED'">
        <div class="published-status">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--neon-gold)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
          <span>已发放，等待数据回填</span>
        </div>
        <CyberButton variant="gold" size="large" block @click="router.push(`/report/${task.id}`)">
          回填数据
        </CyberButton>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { getTask, publishTask, swapTask, autoPublish } from '../api/tasks'
import { track } from '../utils/tracker'
import CyberNav from '../components/CyberNav.vue'
import CyberCard from '../components/CyberCard.vue'
import CyberButton from '../components/CyberButton.vue'

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
  published_at?: string | null
  intent_name?: string
  conversion_scripts?: Record<string, ConversionScriptItem[]> | null
}

const route = useRoute()
const router = useRouter()
const task = ref<Task | null>(null)
const publishState = ref<'idle' | 'publishing' | 'confirming' | 'success' | 'failed'>('idle')

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
    const res = await getTask(route.params.id as string)
    task.value = res.data.task || res.data
  } catch (e) {
    showToast('加载任务失败')
  }
})

const copyText = async (text: string, field?: string) => {
  try {
    await navigator.clipboard.writeText(text)
    track('content_copied', { page: `/task/${task.value?.id}`, metadata: { field: field || 'unknown' } })
    showToast({ message: '已复制', icon: 'checked' })
  } catch {
    showToast('复制失败')
  }
}

const markTaskPublished = (message = '已确认发放') => {
  if (!task.value) return
  task.value.status = 'PUBLISHED'
  task.value.published_at = new Date().toISOString()
  publishState.value = 'success'
  showToast({ message, icon: 'checked' })
}

const handleManualConfirm = async () => {
  if (!task.value) return
  try {
    await showConfirmDialog({
      title: '确认已发放？',
      message: '确认你已经把内容发布到平台，系统会进入数据回填步骤。',
      confirmButtonText: '确认已发放',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  track('publish_clicked', { page: `/task/${task.value.id}`, metadata: { task_id: task.value.id, mode: 'manual_confirm' } })
  publishState.value = 'confirming'
  const toast = showLoadingToast({ message: '确认中...', forbidClick: true, duration: 0 })
  try {
    await publishTask(task.value.id)
    closeToast()
    markTaskPublished()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showToast(detail || '确认失败')
    publishState.value = 'idle'
  } finally {
    closeToast()
  }
}

const handlePublish = async () => {
  if (!task.value) return
  track('publish_clicked', { page: `/task/${task.value.id}`, metadata: { task_id: task.value.id, mode: 'auto' } })
  publishState.value = 'publishing'
  const toast = showLoadingToast({ message: '正在发布...', forbidClick: true, duration: 0 })
  try {
    const res = await autoPublish(task.value.id)
    const data = res.data
    if (data.success) {
      closeToast()
      markTaskPublished('发布成功')
    } else if (data.fallback_to_manual) {
      publishState.value = 'failed'
      closeToast()
      try {
        await showConfirmDialog({
          title: '自动发布不可用',
          message: `${data.error || '自动发布失败'}，是否手动确认发布？\n\n提示：标题和文案已可复制`,
          confirmButtonText: '确认已发布',
          cancelButtonText: '取消',
        })
        await publishTask(task.value.id)
        closeToast()
        markTaskPublished('已确认发放')
      } catch {
        publishState.value = 'idle'
      }
    } else {
      publishState.value = 'failed'
      showToast(data.error || '发布失败')
    }
  } catch (e: any) {
    publishState.value = 'failed'
    closeToast()
    try {
      await showConfirmDialog({
        title: '自动发布失败',
        message: '是否手动确认发布？\n\n提示：标题和文案已可复制',
        confirmButtonText: '确认已发布',
        cancelButtonText: '取消',
      })
      const toast2 = showLoadingToast({ message: '确认中...', forbidClick: true, duration: 0 })
      try {
        await publishTask(task.value.id)
        closeToast()
        markTaskPublished('已确认发放')
      } catch (e2: any) {
        const detail2 = e2?.response?.data?.detail
        showToast(detail2 || '操作失败')
        publishState.value = 'idle'
      } finally {
        closeToast()
      }
    } catch {
      publishState.value = 'idle'
    }
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
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  padding-bottom: 200px;
}

.nav-action-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--ink-gray);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.nav-action-btn:hover {
  color: var(--neon-cyan);
  background: rgba(0, 245, 212, 0.1);
}

.task-content {
  flex: 1;
  padding: 16px var(--page-padding);
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}

.task-header {
  animation: fadeInUp 0.4s ease-out forwards;
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
  font-family: var(--font-mono);
}

.tag-platform {
  background: var(--neon-cyan-dim);
  color: var(--neon-cyan);
  border: 1px solid var(--border-cyan);
}

.tag-optimized {
  background: var(--neon-magenta-dim);
  color: var(--neon-magenta);
  border: 1px solid var(--border-magenta);
}

/* Info Banners */
.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  border-radius: var(--radius-card);
  font-size: 13px;
  line-height: 1.6;
  animation: fadeInUp 0.5s ease-out 0.1s both;
}

.info-banner svg {
  flex-shrink: 0;
  margin-top: 1px;
}

.banner-magenta {
  background: var(--neon-magenta-dim);
  color: var(--neon-magenta);
  border: 1px solid var(--border-magenta);
}

.banner-cyan {
  background: var(--neon-cyan-dim);
  color: var(--neon-cyan);
  border: 1px solid var(--border-cyan);
}

/* Card Header */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.card-bar {
  width: 4px;
  height: 20px;
  border-radius: 2px;
  flex-shrink: 0;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--paper-white);
  margin: 0;
  flex: 1;
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-sm);
  padding: 5px 10px;
  font-size: 12px;
  color: var(--ink-gray);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: var(--font-mono);
}

.copy-btn:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
  background: rgba(0, 245, 212, 0.08);
}

.copy-btn:active {
  transform: scale(0.95);
}

/* Hook */
.hook-content {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--neon-magenta);
  line-height: 1.6;
  padding: 8px 0;
}

/* Storyboard */
.storyboard {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.shot-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.shot-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(155, 93, 229, 0.3), rgba(155, 93, 229, 0.1));
  border: 1px solid rgba(155, 93, 229, 0.4);
  color: var(--neon-purple);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  font-family: var(--font-mono);
}

.shot-info {
  flex: 1;
}

.shot-desc {
  font-size: 14px;
  color: var(--paper-white);
  line-height: 1.6;
}

.shot-duration {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-gray);
  margin-top: 4px;
}

/* Script */
.script-content {
  font-size: 14px;
  color: var(--paper-dim);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* Title */
.title-content {
  font-size: 15px;
  color: var(--neon-gold);
  font-weight: 500;
  line-height: 1.6;
}

/* Comment */
.comment-content {
  background: rgba(255, 214, 10, 0.05);
  padding: 14px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--paper-dim);
  line-height: 1.7;
  border-left: 3px solid var(--neon-gold);
}

/* Conversion */
.conversion-item {
  margin-bottom: 14px;
}

.conversion-item:last-child {
  margin-bottom: 0;
}

.conversion-stage {
  font-size: 13px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 8px;
}

.conversion-text {
  background: rgba(255, 255, 255, 0.03);
  padding: 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--paper-dim);
  line-height: 1.7;
  white-space: pre-wrap;
  border-left: 3px solid;
}

/* Optimization */
.optimization-content {
  background: rgba(255, 214, 10, 0.05);
  padding: 14px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--paper-dim);
  line-height: 1.7;
  border-left: 3px solid var(--neon-gold);
}

/* Loading */
.task-loading {
  flex: 1;
  padding: 16px var(--page-padding);
}

/* Actions */
.task-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px var(--page-padding) 24px;
  background: linear-gradient(180deg, transparent 0%, var(--ink-black) 20%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 50;
}

.manual-publish-hint {
  text-align: center;
  color: var(--ink-gray);
  font-size: 12px;
  line-height: 1.5;
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.published-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: var(--neon-gold);
  font-size: 15px;
  font-weight: 500;
}
</style>
