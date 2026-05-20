<template>
  <div class="report-page">
    <van-nav-bar title="数据回填" left-arrow @click-left="router.back()" />

    <div v-if="task" class="report-content">
      <div class="task-summary">
        <h3>{{ task.title }}</h3>
        <p class="task-meta">{{ task.platform_name }} · {{ formatDate(task.created_at) }}</p>
      </div>

      <van-form @submit="handleSubmit" class="report-form">
        <van-cell-group inset>
          <van-field
            v-model="form.play_count"
            name="play_count"
            label="播放量"
            type="digit"
            placeholder="请输入播放量"
            :rules="[{ required: true, message: '请输入播放量' }]"
          />
          <van-field
            v-model="form.comment_count"
            name="comment_count"
            label="评论数"
            type="digit"
            placeholder="请输入评论数"
            :rules="[{ required: true, message: '请输入评论数' }]"
          />
          <van-field
            v-model="form.message_count"
            name="message_count"
            label="私信数"
            type="digit"
            placeholder="请输入私信数"
            :rules="[{ required: true, message: '请输入私信数' }]"
          />
        </van-cell-group>

        <div class="submit-btn">
          <van-button type="primary" block round size="large" native-type="submit" :loading="submitting">
            提交数据
          </van-button>
        </div>
      </van-form>

      <div v-if="diagnosis" class="diagnosis-result">
        <h3 class="diagnosis-title">📊 诊断结果</h3>
        <div class="diagnosis-card">
          <div class="diagnosis-item">
            <span class="diagnosis-label">问题类型</span>
            <span class="diagnosis-value">{{ diagnosis.problem_desc }}</span>
          </div>
          <div class="diagnosis-item">
            <span class="diagnosis-label">优化方向</span>
            <span class="diagnosis-value">{{ diagnosis.optimization_direction }}</span>
          </div>
          <div class="diagnosis-item">
            <span class="diagnosis-label">优化建议</span>
            <span class="diagnosis-value">{{ diagnosis.optimization_detail }}</span>
          </div>
        </div>
        <van-button
          type="success"
          block
          round
          size="large"
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
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getCurrentTask, reportTask, getDiagnosis, getNextTask as getNextTaskApi } from '../api/tasks'

interface Task {
  id: string
  platform_name: string
  title: string
  created_at: string
  status?: string
}

interface Diagnosis {
  problem_type: string
  problem_desc: string
  optimization_direction: string
  optimization_detail: string
}

const route = useRoute()
const router = useRouter()
const task = ref<Task | null>(null)
const diagnosis = ref<Diagnosis | null>(null)
const submitting = ref(false)

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
  if (!task.value) return
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
  background: #f7f8fa;
}

.report-content {
  padding: 16px;
}

.task-summary {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.task-summary h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px;
}

.task-meta {
  font-size: 13px;
  color: #999;
  margin: 0;
}

.report-form {
  margin-bottom: 16px;
}

.submit-btn {
  padding: 16px;
}

.diagnosis-result {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.diagnosis-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 12px;
}

.diagnosis-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.diagnosis-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.diagnosis-label {
  font-size: 12px;
  color: #999;
}

.diagnosis-value {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.report-loading {
  display: flex;
  justify-content: center;
  padding-top: 100px;
}
</style>
