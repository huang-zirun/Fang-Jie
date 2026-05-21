<template>
  <div class="history-page">
    <div class="custom-nav">
      <div class="nav-back" @click="router.back()">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="nav-title">历史任务</div>
      <div class="nav-placeholder"></div>
    </div>

    <div class="filter-bar">
      <van-dropdown-menu active-color="var(--xh-brand)">
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
            class="task-card"
            @click="router.push(`/task/${task.id}`)"
          >
            <div class="card-top">
              <span class="tag tag-intent" :style="{ background: getIntentBg(task.intent_name), color: getIntentColor(task.intent_name) }">{{ task.intent_name }}</span>
              <span class="tag tag-platform">{{ task.platform_name }}</span>
              <span class="tag tag-status" :style="{ background: getStatusBg(task.status), color: getStatusColor(task.status) }">{{ getStatusLabel(task.status) }}</span>
            </div>
            <div class="card-title">{{ task.title }}</div>
            <div class="card-bottom">
              <span class="card-time">{{ formatDate(task.created_at) }}</span>
              <div v-if="task.play_count != null" class="card-metrics">
                <span class="metric">播放 {{ task.play_count }}</span>
                <span class="metric">评论 {{ task.comment_count }}</span>
                <span class="metric">私信 {{ task.message_count }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="!loading" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">还没有历史任务，去选择一个赚钱目标吧</div>
          <van-button
            type="primary"
            round
            size="small"
            color="var(--xh-brand)"
            @click="router.push('/')"
          >
            去选择
          </van-button>
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
  problem_desc: string | null
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
    '引流拿客户': '#FF2442',
    '成交赚钱': '#FF8C00',
    '裂变招募分销': '#4A90D9',
    'IP长期增长': '#8B5CF6',
  }
  return map[name] || '#FF2442'
}

const getIntentBg = (name: string): string => {
  const map: Record<string, string> = {
    '引流拿客户': '#fff0f2',
    '成交赚钱': '#fff7ed',
    '裂变招募分销': '#eff6ff',
    'IP长期增长': '#f5f3ff',
  }
  return map[name] || '#fff0f2'
}

const getStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: '#4A90D9',
    PUBLISHED: '#FF8C00',
    REPORTED: '#8B5CF6',
    DIAGNOSED: '#10B981',
    EXPIRED: '#999999',
  }
  return map[status] || '#999999'
}

const getStatusBg = (status: string): string => {
  const map: Record<string, string> = {
    PENDING: '#eff6ff',
    PUBLISHED: '#fff7ed',
    REPORTED: '#f5f3ff',
    DIAGNOSED: '#ecfdf5',
    EXPIRED: '#f5f5f5',
  }
  return map[status] || '#f5f5f5'
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
  background: var(--xh-bg-secondary);
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

.nav-placeholder {
  width: 36px;
}

.filter-bar {
  position: sticky;
  top: 48px;
  z-index: 99;
}

.task-list {
  padding: 12px 16px;
}

.task-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 16px;
  margin-bottom: 10px;
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all 0.15s ease;
}

.task-card:active {
  transform: scale(0.98);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-tag);
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.tag-platform {
  background: var(--xh-bg-secondary);
  color: var(--xh-text-secondary);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--xh-text-primary);
  line-height: 1.4;
  margin-bottom: 10px;
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
  font-size: 12px;
  color: var(--xh-text-tertiary);
}

.card-metrics {
  display: flex;
  gap: 10px;
}

.metric {
  font-size: 11px;
  color: var(--xh-text-tertiary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 32px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  line-height: 1;
}

.empty-text {
  font-size: 14px;
  color: var(--xh-text-tertiary);
  margin-bottom: 20px;
  text-align: center;
}
</style>
