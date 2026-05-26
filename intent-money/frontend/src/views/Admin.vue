<template>
  <div class="admin-page">
    <CyberNav title="运营后台" />

    <van-tabs v-model:active="activeTab" class="admin-tabs">
      <van-tab title="今日概览">
        <div class="tab-content">
          <!-- Stats Grid -->
          <div class="stats-grid">
            <div class="stat-card" style="--stat-color: var(--neon-cyan); --stat-bg: rgba(0, 245, 212, 0.1)">
              <div class="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div class="stat-value">{{ stats.today_tasks }}</div>
              <div class="stat-label">今日任务</div>
            </div>
            <div class="stat-card" style="--stat-color: var(--neon-magenta); --stat-bg: rgba(255, 0, 110, 0.1)">
              <div class="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--neon-magenta)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <div class="stat-value">{{ stats.today_published }}</div>
              <div class="stat-label">已发布</div>
            </div>
            <div class="stat-card" style="--stat-color: var(--neon-gold); --stat-bg: rgba(255, 214, 10, 0.1)">
              <div class="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--neon-gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <div class="stat-value">{{ stats.today_pending }}</div>
              <div class="stat-label">待处理</div>
            </div>
            <div class="stat-card" style="--stat-color: var(--neon-purple); --stat-bg: rgba(155, 93, 229, 0.1)">
              <div class="stat-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--neon-purple)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
              </div>
              <div class="stat-value">{{ stats.today_swapped }}</div>
              <div class="stat-label">已换条</div>
            </div>
          </div>

          <!-- Intent Distribution -->
          <CyberCard>
            <div class="card-header">
              <div class="card-bar" style="background: var(--neon-cyan)"></div>
              <h3 class="card-title">意图分布</h3>
            </div>
            <div class="intent-bars">
              <div v-for="item in stats.intent_distribution" :key="item.intent_name" class="intent-bar">
                <div class="intent-bar-label">{{ item.intent_name }}</div>
                <div class="intent-bar-track">
                  <div
                    class="intent-bar-fill"
                    :style="{
                      width: `${(item.count / (stats.today_tasks || 1)) * 100}%`,
                      background: getIntentColor(item.intent_name)
                    }"
                  ></div>
                </div>
                <div class="intent-bar-value">{{ item.count }}</div>
              </div>
            </div>
          </CyberCard>
        </div>
      </van-tab>

      <van-tab title="问题统计">
        <div class="tab-content">
          <CyberCard>
            <div class="card-header">
              <div class="card-bar" style="background: var(--neon-magenta)"></div>
              <h3 class="card-title">问题分布</h3>
            </div>
            <div class="problem-list">
              <div v-for="item in stats.problem_stats" :key="item.problem_type" class="problem-item">
                <div class="problem-label">{{ item.problem_type }}</div>
                <div class="problem-bar-track">
                  <div
                    class="problem-bar-fill"
                    :style="{ width: `${(item.count / (stats.total_problems || 1)) * 100}%` }"
                  ></div>
                </div>
                <div class="problem-value">{{ item.count }}</div>
              </div>
            </div>
          </CyberCard>
        </div>
      </van-tab>

      <van-tab title="任务列表">
        <div class="tab-content">
          <div class="task-list">
            <div v-for="task in tasks" :key="task.id" class="admin-task-card">
              <div class="task-top">
                <span class="tag" :style="{ background: getIntentBg(task.intent_name), color: getIntentColor(task.intent_name) }">
                  {{ task.intent_name }}
                </span>
                <span class="tag tag-platform">{{ task.platform_name }}</span>
              </div>
              <div class="task-title">{{ task.title }}</div>
              <div class="task-data">
                <span v-if="task.play_count != null">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  {{ task.play_count }}
                </span>
                <span v-if="task.comment_count != null">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                  </svg>
                  {{ task.comment_count }}
                </span>
                <span v-if="task.message_count != null">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                  {{ task.message_count }}
                </span>
                <span class="task-status" :style="{ color: getStatusColor(task.status) }">{{ getStatusLabel(task.status) }}</span>
              </div>
              <div v-if="task.problem_type" class="task-problem">{{ task.problem_type }}</div>
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { getTaskOverview, getTaskHistory } from '../api/tasks'
import CyberNav from '../components/CyberNav.vue'
import CyberCard from '../components/CyberCard.vue'

interface Stats {
  today_tasks: number
  today_published: number
  today_pending: number
  today_swapped: number
  total_problems: number
  intent_distribution: { intent_name: string; count: number }[]
  problem_stats: { problem_type: string; count: number }[]
}

interface AdminTask {
  id: string
  intent_name: string
  platform_name: string
  status: string
  title: string
  play_count: number | null
  comment_count: number | null
  message_count: number | null
  problem_type: string | null
}

const activeTab = ref(0)
const stats = ref<Stats>({
  today_tasks: 0,
  today_published: 0,
  today_pending: 0,
  today_swapped: 0,
  total_problems: 0,
  intent_distribution: [],
  problem_stats: [],
})
const tasks = ref<AdminTask[]>([])

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

onMounted(async () => {
  try {
    const statsRes = await getTaskOverview()
    stats.value = statsRes.data
  } catch {
    showToast('加载统计失败')
  }

  try {
    const tasksRes = await getTaskHistory()
    tasks.value = tasksRes.data.tasks || tasksRes.data
  } catch {
    showToast('加载任务失败')
  }
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.tab-content {
  padding: 16px var(--page-padding) 40px;
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 20px 16px;
  text-align: center;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--stat-color);
  opacity: 0.6;
}

.stat-card:hover {
  border-color: var(--stat-color);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 15px var(--stat-bg);
}

.stat-icon {
  margin-bottom: 10px;
}

.stat-value {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 700;
  color: var(--stat-color);
  line-height: 1;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--ink-gray);
  font-weight: 500;
}

/* Intent Bars */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
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
}

.intent-bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.intent-bar {
  display: grid;
  grid-template-columns: 80px 1fr 32px;
  align-items: center;
  gap: 12px;
}

.intent-bar-label {
  font-size: 13px;
  color: var(--paper-white);
  font-weight: 500;
}

.intent-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.intent-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.intent-bar-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-gray);
  text-align: right;
}

/* Problem List */
.problem-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.problem-item {
  display: grid;
  grid-template-columns: 100px 1fr 32px;
  align-items: center;
  gap: 12px;
}

.problem-label {
  font-size: 12px;
  color: var(--paper-white);
  font-weight: 500;
}

.problem-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.problem-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-magenta), #ff4d6d);
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.problem-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-gray);
  text-align: right;
}

/* Task List */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-task-card {
  background: var(--gradient-card);
  border: 1px solid var(--border-gray);
  border-radius: var(--radius-card);
  padding: 16px;
}

.task-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-tag);
  font-size: 11px;
  font-weight: 500;
  font-family: var(--font-mono);
}

.tag-platform {
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink-gray);
  border: 1px solid var(--border-gray);
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--paper-white);
  line-height: 1.5;
  margin-bottom: 10px;
}

.task-data {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--ink-gray);
  font-family: var(--font-mono);
}

.task-data span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-status {
  margin-left: auto;
  font-weight: 500;
}

.task-problem {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(255, 0, 110, 0.08);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--neon-magenta);
  border-left: 2px solid var(--neon-magenta);
}
</style>
