<template>
  <div class="report-page">
    <CyberNav title="数据回填" />

    <div v-if="task" class="report-content">
      <!-- Task Summary -->
      <CyberCard>
        <div class="summary-title">{{ task.title }}</div>
        <div class="summary-meta">
          <span class="meta-platform">{{ task.platform_name }}</span>
          <span class="meta-divider">·</span>
          <span class="meta-date">{{ formatDate(task.created_at) }}</span>
        </div>
      </CyberCard>

      <!-- Form Card -->
      <CyberCard variant="cyan" glow-border glow-color="cyan">
        <div class="card-header">
          <div class="card-bar" style="background: var(--neon-cyan)"></div>
          <h3 class="card-title">填写数据</h3>
        </div>
        <van-form @submit="handleSubmit" class="report-form">
          <div class="form-field">
            <label class="field-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              {{ playCountLabel }}
            </label>
            <van-field
              v-model="form.play_count"
              name="play_count"
              type="digit"
              :placeholder="`请输入${playCountLabel}`"
              required
              class="custom-field"
            />
          </div>
          <div class="form-field">
            <label class="field-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
              </svg>
              评论数
            </label>
            <van-field
              v-model="form.comment_count"
              name="comment_count"
              type="digit"
              placeholder="请输入评论数"
              required
              class="custom-field"
            />
          </div>
          <div class="form-field">
            <label class="field-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              私信数
            </label>
            <van-field
              v-model="form.message_count"
              name="message_count"
              type="digit"
              placeholder="请输入私信数"
              required
              class="custom-field"
            />
          </div>

          <div class="submit-btn">
            <CyberButton variant="primary" size="large" block :loading="submitting" @click="handleSubmit">
              提交数据
            </CyberButton>
          </div>
        </van-form>
      </CyberCard>

      <!-- Diagnosis Section -->
      <div v-if="diagnosis" class="diagnosis-section">
        <CyberCard variant="purple" glow-border glow-color="purple">
          <div class="card-header">
            <div class="card-bar" style="background: var(--neon-purple)"></div>
            <h3 class="card-title">诊断结果</h3>
          </div>

          <div class="diagnosis-grid">
            <div class="diagnosis-item">
              <div class="diagnosis-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--neon-magenta)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div class="diagnosis-label">问题类型</div>
              <div class="diagnosis-value">{{ diagnosis.problem_desc }}</div>
            </div>

            <div class="diagnosis-item">
              <div class="diagnosis-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
              <div class="diagnosis-label">优化方向</div>
              <div class="diagnosis-value">{{ diagnosis.optimization_direction }}</div>
            </div>

            <div class="diagnosis-item">
              <div class="diagnosis-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--neon-gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/>
                  <path d="M9 21h6"/>
                </svg>
              </div>
              <div class="diagnosis-label">优化建议</div>
              <div class="diagnosis-value">{{ diagnosis.optimization_detail }}</div>
            </div>
          </div>
        </CyberCard>

        <!-- AI Analysis -->
        <CyberCard v-if="aiAnalysis" variant="purple" glow-border glow-color="purple" style="margin-top: 16px">
          <div class="card-header">
            <div class="card-bar" style="background: var(--neon-purple)"></div>
            <h3 class="card-title">AI 深度分析</h3>
          </div>
          <div v-if="aiAnalysis.root_cause" class="ai-analysis-item">
            <div class="ai-label">根因分析</div>
            <div class="ai-value">{{ aiAnalysis.root_cause }}</div>
          </div>
          <div v-if="aiAnalysis.specific_suggestions?.length" class="ai-analysis-item">
            <div class="ai-label">具体建议</div>
            <ul class="ai-suggestions">
              <li v-for="(s, idx) in aiAnalysis.specific_suggestions" :key="idx">{{ s }}</li>
            </ul>
          </div>
          <div v-if="aiAnalysis.confidence != null" class="ai-analysis-item">
            <div class="ai-label">置信度</div>
            <div class="confidence-bar">
              <div class="confidence-fill" :style="{ width: `${aiAnalysis.confidence * 100}%` }"></div>
            </div>
            <div class="confidence-text">{{ Math.round(aiAnalysis.confidence * 100) }}%</div>
          </div>
        </CyberCard>

        <CyberButton variant="gold" size="large" block style="margin-top: 16px" @click="getNextTask">
          获取下一条优化任务
        </CyberButton>
      </div>
    </div>

    <div v-else class="report-loading">
      <van-loading size="36px" vertical>加载中...</van-loading>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showDialog } from 'vant'
import { getCurrentTask, getTask, reportTask, getDiagnosis, getNextTask as getNextTaskApi } from '../api/tasks'
import CyberNav from '../components/CyberNav.vue'
import CyberCard from '../components/CyberCard.vue'
import CyberButton from '../components/CyberButton.vue'

interface Task {
  id: string
  intent_id?: string
  platform_id?: string
  platform_name: string
  title: string
  created_at: string
  status?: string
  task_type?: string
}

interface AiAnalysisData {
  root_cause?: string
  specific_suggestions?: string[]
  confidence?: number
}

interface Diagnosis {
  problem_type: string
  problem_desc: string
  optimization_direction: string
  optimization_detail: string
  ai_analysis?: string | AiAnalysisData
  rule_confidence?: number
}

const route = useRoute()
const router = useRouter()
const task = ref<Task | null>(null)
const diagnosis = ref<Diagnosis | null>(null)
const submitting = ref(false)

const aiAnalysis = computed<AiAnalysisData | null>(() => {
  if (!diagnosis.value?.ai_analysis) return null
  if (typeof diagnosis.value.ai_analysis === 'string') {
    try {
      return JSON.parse(diagnosis.value.ai_analysis)
    } catch {
      return null
    }
  }
  return diagnosis.value.ai_analysis
})

const playCountLabel = computed(() => {
  if (task.value?.platform_name?.includes('小红书')) {
    return '阅读量'
  }
  return '播放量'
})

const form = ref({
  play_count: '',
  comment_count: '',
  message_count: '',
})

onMounted(async () => {
  try {
    const routeTaskId = route.params.id as string | undefined
    const res = routeTaskId ? await getTask(routeTaskId) : await getCurrentTask()
    task.value = res.data.task || res.data

    if (task.value?.status === 'DIAGNOSED') {
      const diagnosisRes = await getDiagnosis(task.value.id)
      diagnosis.value = diagnosisRes.data.diagnosis || diagnosisRes.data
    }
  } catch (e) {
    showToast('加载任务失败')
  }
})

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const handleSubmit = async () => {
  if (!task.value) return
  if (!form.value.play_count || !form.value.comment_count || !form.value.message_count) {
    showToast('请填写所有数据')
    return
  }
  submitting.value = true
  try {
    const res = await reportTask(task.value.id, {
      play_count: parseInt(form.value.play_count) || 0,
      comment_count: parseInt(form.value.comment_count) || 0,
      message_count: parseInt(form.value.message_count) || 0,
    })
    diagnosis.value = res.data.diagnosis || res.data
    showToast({ message: '数据提交成功', icon: 'checked' })
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    showToast(detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

const getNextTask = async () => {
  if (!task.value || !diagnosis.value) return

  const suggestions = aiAnalysis.value?.specific_suggestions
    ? aiAnalysis.value.specific_suggestions.join('\n')
    : diagnosis.value.optimization_detail

  try {
    await showDialog({
      title: '优化方案确认',
      message: `问题：${diagnosis.value.problem_desc}\n\n优化方向：${diagnosis.value.optimization_direction}\n\n具体措施：${suggestions}\n\n预期效果：优化后${playCountLabel}预计提升30%+`,
      confirmButtonText: '确认生成',
      confirmButtonColor: 'var(--neon-gold)',
      showCancelButton: true,
      cancelButtonText: '再想想',
    })
  } catch {
    return
  }

  const toast = showLoadingToast({ message: '生成优化任务...', forbidClick: true, duration: 0 })
  try {
    const res = await getNextTaskApi(task.value.id, {
      platform_id: task.value.platform_id,
      task_type: task.value.task_type || 'video',
    })
    const newTask = res.data.task || res.data
    closeToast()
    router.push(`/task/${newTask.id}`)
  } catch (e: any) {
    closeToast()
    const detail = e?.response?.data?.detail
    showToast(detail || '获取失败')
  }
}
</script>

<style scoped>
.report-page {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.report-content {
  padding: 16px var(--page-padding) 40px;
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}

/* Summary */
.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-white);
  margin: 0 0 10px;
  line-height: 1.4;
}

.summary-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-gray);
}

.meta-platform {
  color: var(--neon-cyan);
  font-family: var(--font-mono);
}

.meta-divider {
  opacity: 0.5;
}

/* Form */
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

.report-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--paper-white);
}

.field-label svg {
  color: var(--neon-cyan);
}

.custom-field {
  background: rgba(26, 26, 46, 0.6);
  border-radius: var(--radius-input);
  border: 1px solid var(--border-gray);
  overflow: hidden;
  transition: all 0.2s ease;
}

.custom-field:focus-within {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 12px rgba(0, 245, 212, 0.15);
}

.custom-field :deep(.van-field__control) {
  font-size: 15px;
  color: var(--paper-white);
  padding: 12px 14px;
}

.custom-field :deep(.van-field__error-message) {
  font-size: 12px;
  padding: 4px 14px 0;
  color: var(--neon-magenta);
}

.submit-btn {
  margin-top: 8px;
}

/* Diagnosis */
.diagnosis-section {
  animation: fadeInUp 0.5s ease-out forwards;
}

.diagnosis-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.diagnosis-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--neon-purple);
}

.diagnosis-icon {
  margin-bottom: 4px;
}

.diagnosis-label {
  font-size: 12px;
  color: var(--ink-gray);
  font-weight: 500;
  font-family: var(--font-mono);
}

.diagnosis-value {
  font-size: 14px;
  color: var(--paper-white);
  line-height: 1.6;
}

/* AI Analysis */
.ai-analysis-item {
  margin-bottom: 14px;
}

.ai-analysis-item:last-child {
  margin-bottom: 0;
}

.ai-label {
  font-size: 12px;
  color: var(--ink-gray);
  font-weight: 500;
  margin-bottom: 6px;
  font-family: var(--font-mono);
}

.ai-value {
  font-size: 14px;
  color: var(--paper-dim);
  line-height: 1.7;
}

.ai-suggestions {
  margin: 6px 0 0 18px;
  padding: 0;
}

.ai-suggestions li {
  font-size: 14px;
  color: var(--paper-dim);
  line-height: 1.8;
}

.confidence-bar {
  height: 8px;
  background: rgba(155, 93, 229, 0.15);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 6px;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-purple), #c4b5fd);
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.confidence-text {
  font-size: 12px;
  color: var(--neon-purple);
  font-weight: 600;
  text-align: right;
  margin-top: 4px;
  font-family: var(--font-mono);
}

/* Loading */
.report-loading {
  display: flex;
  justify-content: center;
  padding-top: 100px;
}
</style>
