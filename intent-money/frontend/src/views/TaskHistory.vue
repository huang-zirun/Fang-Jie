<template>
  <div class="history-page">
    <CyberNav title="历史任务" />

    <div class="filter-bar">
      <van-dropdown-menu active-color="var(--neon-cyan)">
        <van-dropdown-item v-model="filterIntent" :options="intentOptions" @change="onFilterChange" />
        <van-dropdown-item v-model="filterStatus" :options="statusOptions" @change="onFilterChange" />
      </van-dropdown-menu>
    </div>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text=""
        @load="onLoad"
      >
        <div v-if="tasks.length > 0" class="task-list">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="history-card"
            @click="router.push(`/task/${task.id}`)"
          >
            <div class="card-glow" :style="{ background: getIntentColor(task.intent_name) }"></div>
            <div class="card-top">
              <span class="tag tag-intent" :style="{ background: getIntentBg(task.intent_name), color: getIntentColor(task.intent_name), borderColor: getIntentColor(task.intent_name) + '40' }">
                {{ task.intent_name }}
              </span>
              <span class="tag tag-platform">{{ task.platform_name }}</span>
              <span class="tag tag-status" :style="{ background: getStatusBg(task.status), color: getStatusColor(task.status) }">
                {{ getStatusLabel(task.status) }}
              </span>
            </div>
            <div class="card-title">{{ task.title }}</div>
            <div class="card-bottom">
              <span class="card-time">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ formatDate(task.created_at) }}
              </span>
              <div v-if="task.play_count != null" class="card-metrics">
                <span class="metric">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  {{ task.play_count }}
                </span>
                <span class="metric">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                  </svg>
                  {{ task.comment_count }}
                </span>
                <span class="metric">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                  {{ task.message_count }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="!loading" class="empty-state">
          <div class="empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--ink-gray)" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="empty-text">还没有历史任务</div>
          <div class="empty-sub">去选择一个赚钱目标，开始你的第一条内容</div>
          <CyberButton variant="primary" size="default" @click="router.push('/')">
            去选择
          </CyberButton>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getTaskHistory } from '../api/tasks'
import CyberNav from '../components/CyberNav.vue'
import CyberButton from '../components/CyberButton.vue'

interface TaskHistoryItem {
  id: string
  intent_name: string
  platform_name: string
  status: string
  task_type: string
  hook_text: string
  title: string
  created_at: string
  published_at: string | null
  problem_type: string | null
  play_count: number | null
  comment_count: number | null
  message_count: number | null
}

const router = useRouter()
const tasks = ref<TaskHistoryItem[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const filterIntent = ref('')
const filterStatus = ref('')

const intentOptions = [
  { text: '全部意图', value: '' },
  { text: '引流拿客户', value: '引流拿客户' },
  { text: '成交赚钱', value: '成交赚钱' },
  { text: '裂变招募分销', value: '裂变招募分销' },
  { text: 'IP长期增长', value: 'IP长期增长' },
]

const statusOptions = [
  { text: '全部状态', value: '' },
  { text: '待发布', value: 'PENDING' },
  { text: '已发布', value: 'PUBLISHED' },
  { text: '已回填', value: 'REPORTED' },
  { text: '已诊断', value: 'DIAGNOSED' },
  { text: '已过期', value: 'EXPIRED' },
]

const getIntentColor = (name: string): string => {
  const map: Record<string, string> = {
    '引流拿客户': '#00f5d4',
    '成交赚钱': '#ff006e',
    '裂变招募分销': '#ffd60a',
    'IP长期增长': '#9b5de5',
  }
  return map[name] || '#00f5d4'
}

const getIntentBg = (name: string): string => {
  const map: Record<string, string> = {
    '引流拿客户': 'rgba(0, 245, 212, 0.1)',
    '成交赚钱': 'rgba(255, 0, 110, 0.1)',
    '裂变招募分销': 'rgba(255, 214, 10, 0.1)',
    'IP长期增长': 'rgba(155, 93, 229, 0.1)',
  }
  return map[name] || 'rgba(0, 245, 212, 0.1)'
}

const getStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: '#00f5d4',
    PUBLISHED: '#ffd60a',
    REPORTED: '#9b5de5',
    DIAGNOSED: '#00f5d4',
    EXPIRED: '#8b8b9e',
  }
  return map[status] || '#8b8b9e'
}

const getStatusBg = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: 'rgba(0, 245, 212, 0.1)',
    PUBLISHED: 'rgba(255, 214, 10, 0.1)',
    REPORTED: 'rgba(155, 93, 229, 0.1)',
    DIAGNOSED: 'rgba(0, 245, 212, 0.1)',
    EXPIRED: 'rgba(139, 139, 158, 0.1)',
  }
  return map[status] || 'rgba(139, 139, 158, 0.1)'
}

const getStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: '待发布',
    PUBLISHED: '已发布',
    REPORTED: '已回填',
    DIAGNOSED: '已诊断',
    EXPIRED: '已过期',
  }
  return map[status] || status
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fetchTasks = async () => {
  try {
    const params: Record<string, string> = {}
    if (filterIntent.value) params.intent_name = filterIntent.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await getTaskHistory(params)
    tasks.value = res.data.tasks || res.data
    finished.value = true
  } catch (e) {
    showToast('加载失败')
    finished.value = true
  }
}

const onLoad = async () => {
  await fetchTasks()
  loading.value = false
}

const onRefresh = async () => {
  finished.value = false
  loading.value = true
  await fetchTasks()
  refreshing.value = false
  loading.value = false
}

const onFilterChange = async () => {
  tasks.value = []
  finished.value = false
  loading.value = true
  await fetchTasks()
  loading.value = false
}
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.filter-bar {
  position: sticky;
  top: 56px;
  z-index: 99;
}

.task-list {
  padding: 12px var(--page-padding) 40px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  position: relative;
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.card-glow {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.history-card:hover {
  transform: translateX(3px);
  border-color: var(--border-cyan);
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
}

.history-card:hover .card-glow {
  opacity: 1;
}

.history-card:active {
  transform: scale(0.98);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-tag);
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  font-family: var(--font-mono);
}

.tag-intent {
  border: 1px solid;
}

.tag-platform {
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink-gray);
  border: 1px solid var(--border-gray);
}

.tag-status {
  border: 1px solid transparent;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--paper-white);
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--ink-gray);
  font-family: var(--font-mono);
}

.card-metrics {
  display: flex;
  gap: 12px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--ink-gray);
  font-family: var(--font-mono);
}

.metric svg {
  opacity: 0.7;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 32px;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-white);
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 13px;
  color: var(--ink-gray);
  margin-bottom: 24px;
  text-align: center;
}
</style>
