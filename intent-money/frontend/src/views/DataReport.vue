<template>
  <div class="report-page">
    <div class="custom-nav">
      <div class="nav-back" @click="router.back()">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="nav-title">数据回填</div>
      <div class="nav-placeholder"></div>
    </div>

    <div v-if="task" class="report-content">
      <div class="task-summary">
        <h3 class="summary-title">{{ task.title }}</h3>
        <p class="summary-meta">{{ task.platform_name }} · {{ formatDate(task.created_at) }}</p>
      </div>

      <div class="form-card">
        <div class="card-header">
          <div class="card-bar" style="background: var(--xh-brand)"></div>
          <h3 class="card-title">填写数据</h3>
        </div>
        <van-form @submit="handleSubmit" class="report-form">
          <div class="form-field">
            <label class="field-label">播放量</label>
            <van-field
              v-model="form.play_count"
              name="play_count"
              type="digit"
              placeholder="请输入播放量"
              required
              class="custom-field"
            />
          </div>
          <div class="form-field">
            <label class="field-label">评论数</label>
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
            <label class="field-label">私信数</label>
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
            <van-button
              type="primary"
              block
              round
              size="large"
              color="var(--xh-brand)"
              native-type="submit"
              :loading="submitting"
            >
              提交数据
            </van-button>
          </div>
        </van-form>
      </div>

      <div v-if="diagnosis" class="diagnosis-section">
        <div class="card-header" style="margin-bottom: 12px">
          <div class="card-bar" style="background: #8b5cf6"></div>
          <h3 class="card-title">诊断结果</h3>
        </div>

        <div class="diagnosis-card">
          <div class="diagnosis-icon">
            <van-icon name="warning-o" size="24" color="var(--xh-warning)" />
          </div>
          <div class="diagnosis-body">
            <div class="diagnosis-label">问题类型</div>
            <div class="diagnosis-value">{{ diagnosis.problem_desc }}</div>
          </div>
        </div>

        <div class="diagnosis-card">
          <div class="diagnosis-icon">
            <van-icon name="aim" size="24" color="#8b5cf6" />
          </div>
          <div class="diagnosis-body">
            <div class="diagnosis-label">优化方向</div>
            <div class="diagnosis-value">{{ diagnosis.optimization_direction }}</div>
          </div>
        </div>

        <div class="diagnosis-card">
          <div class="diagnosis-icon">
            <van-icon name="bulb-o" size="24" color="#06b6d4" />
          </div>
          <div class="diagnosis-body">
            <div class="diagnosis-label">优化建议</div>
            <div class="diagnosis-value">{{ diagnosis.optimization_detail }}</div>
          </div>
        </div>

        <div v-if="aiAnalysis" class="ai-analysis-card">
          <div class="card-header" style="margin-bottom: 12px">
            <div class="card-bar" style="background: #8B5CF6"></div>
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
        </div>

        <van-button
          type="success"
          block
          round
          size="large"
          color="var(--xh-success)"
          style="margin-top: 16px"
          @click="getNextTask"
        >
          获取下一条优化任务
        </van-button>
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
import { getCurrentTask, reportTask, getDiagnosis, getNextTask as getNextTaskApi } from '../api/tasks'

interface Task {
  id: string
  platform_name: string
  title: string
  created_at: string
  status?: string
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

const form = ref({
  play_count: '',
  comment_count: '',
  message_count: '',
})

onMounted(async () => {
  try {
    const res = await getCurrentTask()
    task.value = res.data.task || res.data
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
      message: `问题：${diagnosis.value.problem_desc}\n\n优化方向：${diagnosis.value.optimization_direction}\n\n具体措施：${suggestions}\n\n预期效果：优化后播放量预计提升30%+`,
      confirmButtonText: '确认生成',
      confirmButtonColor: 'var(--xh-success)',
      showCancelButton: true,
      cancelButtonText: '再想想',
    })
  } catch {
    return
  }

  const toast = showLoadingToast({ message: '生成优化任务...', forbidClick: true, duration: 0 })
  try {
    const res = await getNextTaskApi(task.value.id, {
      platform_id: '10000000-0000-0000-0000-000000000001',
      task_type: 'video',
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

.report-content {
  padding: 16px;
}

.task-summary {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 20px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-card);
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--xh-text-primary);
  margin: 0 0 8px;
  line-height: 1.4;
}

.summary-meta {
  font-size: 13px;
  color: var(--xh-text-tertiary);
  margin: 0;
}

.form-card {
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
  margin-bottom: 16px;
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
}

.report-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--xh-text-primary);
}

.custom-field {
  background: var(--xh-bg-secondary);
  border-radius: var(--radius-input);
  overflow: hidden;
}

.custom-field :deep(.van-field__control) {
  font-size: 15px;
  color: var(--xh-text-primary);
}

.custom-field :deep(.van-field__error-message) {
  font-size: 12px;
  padding-top: 4px;
}

.submit-btn {
  margin-top: 8px;
}

.diagnosis-section {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 16px;
  margin-top: 12px;
  box-shadow: var(--shadow-card);
}

.diagnosis-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: var(--xh-bg-secondary);
  border-radius: var(--radius-input);
  margin-bottom: 10px;
}

.diagnosis-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.diagnosis-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.diagnosis-label {
  font-size: 12px;
  color: var(--xh-text-tertiary);
  font-weight: 500;
}

.diagnosis-value {
  font-size: 14px;
  color: var(--xh-text-primary);
  line-height: 1.5;
}

.report-loading {
  display: flex;
  justify-content: center;
  padding-top: 100px;
}

.ai-analysis-card {
  background: #f5f3ff;
  border-radius: var(--radius-input);
  padding: 14px;
  margin-top: 10px;
  border-left: 3px solid #8B5CF6;
}

.ai-analysis-item {
  margin-bottom: 12px;
}

.ai-analysis-item:last-child {
  margin-bottom: 0;
}

.ai-label {
  font-size: 12px;
  color: var(--xh-text-tertiary);
  font-weight: 500;
  margin-bottom: 4px;
}

.ai-value {
  font-size: 14px;
  color: var(--xh-text-primary);
  line-height: 1.6;
}

.ai-suggestions {
  margin: 4px 0 0 16px;
  padding: 0;
}

.ai-suggestions li {
  font-size: 14px;
  color: var(--xh-text-secondary);
  line-height: 1.8;
}

.confidence-bar {
  height: 8px;
  background: #ede9fe;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #8B5CF6, #a78bfa);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.confidence-text {
  font-size: 12px;
  color: #8B5CF6;
  font-weight: 600;
  text-align: right;
  margin-top: 2px;
}
</style>
