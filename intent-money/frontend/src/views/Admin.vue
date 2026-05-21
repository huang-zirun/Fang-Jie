<template>
  <div class="admin-page">
    <div class="custom-nav">
      <div class="nav-back" @click="router.back()">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="nav-title">运营后台</div>
      <div class="nav-placeholder"></div>
    </div>

    <van-tabs v-model:active="activeTab" sticky offset-top="48" color="var(--xh-brand)" title-active-color="var(--xh-brand)">
      <van-tab title="数据概览">
        <div class="tab-content">
          <van-loading v-if="statsLoading" class="section-loading" />
          <template v-else>
            <van-grid :column-num="2" :border="false" gutter="12">
              <van-grid-item>
                <div class="stat-card stat-pink">
                  <div class="stat-value">{{ stats.total_users }}</div>
                  <div class="stat-label">总用户数</div>
                </div>
              </van-grid-item>
              <van-grid-item>
                <div class="stat-card stat-orange">
                  <div class="stat-value">{{ stats.total_tasks }}</div>
                  <div class="stat-label">总任务数</div>
                </div>
              </van-grid-item>
              <van-grid-item>
                <div class="stat-card stat-blue">
                  <div class="stat-value">{{ stats.publish_rate }}%</div>
                  <div class="stat-label">发布率</div>
                </div>
              </van-grid-item>
              <van-grid-item>
                <div class="stat-card stat-green">
                  <div class="stat-value">{{ stats.report_rate }}%</div>
                  <div class="stat-label">回填率</div>
                </div>
              </van-grid-item>
            </van-grid>
          </template>
        </div>
      </van-tab>

      <van-tab title="内容结构">
        <div class="tab-content">
          <van-loading v-if="structuresLoading" class="section-loading" />
          <template v-else>
            <div v-for="item in structures" :key="item.id" class="admin-card">
              <div class="card-row">
                <span class="card-label">意图</span>
                <span class="card-value">{{ item.intent_name }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">平台</span>
                <span class="card-value">{{ item.platform_name }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">钩子类型</span>
                <span class="card-value">{{ item.hook_type }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">优先级</span>
                <span class="card-value">{{ item.priority }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">市场评分</span>
                <div class="inline-edit">
                  <van-field
                    v-model="item._editScore"
                    type="number"
                    class="score-input"
                    :border="false"
                  />
                  <van-button
                    size="mini"
                    round
                    color="var(--xh-brand)"
                    @click="saveStructureScore(item)"
                  >
                    保存
                  </van-button>
                </div>
              </div>
            </div>
            <div v-if="structures.length === 0" class="empty-hint">暂无内容结构</div>
          </template>
        </div>
      </van-tab>

      <van-tab title="转化路径">
        <div class="tab-content">
          <van-loading v-if="pathsLoading" class="section-loading" />
          <template v-else>
            <div class="section-actions">
              <van-button size="small" round color="var(--xh-brand)" @click="openPathDialog()">
                新增路径
              </van-button>
            </div>
            <div v-for="(paths, intentName) in pathsByIntent" :key="intentName" class="intent-group">
              <div class="group-title">{{ intentName }}</div>
              <div v-for="path in paths" :key="path.id" class="admin-card">
                <div class="card-row">
                  <span class="stage-tag" :style="{ background: getStageBg(path.stage), color: getStageColor(path.stage) }">
                    {{ getStageLabel(path.stage) }}
                  </span>
                </div>
                <div class="card-row">
                  <span class="card-label">标题</span>
                  <span class="card-value">{{ path.title }}</span>
                </div>
                <div class="card-row">
                  <span class="card-label">话术</span>
                  <span class="card-value script-preview">{{ path.script_preview }}</span>
                </div>
                <div class="card-actions">
                  <van-button size="mini" plain round color="var(--xh-brand)" @click="openPathDialog(path)">
                    编辑
                  </van-button>
                  <van-button size="mini" plain round color="#999" @click="handleDeletePath(path.id)">
                    删除
                  </van-button>
                </div>
              </div>
            </div>
            <div v-if="Object.keys(pathsByIntent).length === 0" class="empty-hint">暂无转化路径</div>
          </template>
        </div>
      </van-tab>

      <van-tab title="市场热点">
        <div class="tab-content">
          <van-loading v-if="hotsLoading" class="section-loading" />
          <template v-else>
            <div class="section-actions">
              <van-button size="small" round color="var(--xh-brand)" @click="showHotDialog = true">
                添加热点
              </van-button>
              <van-button size="small" round plain color="var(--xh-brand)" @click="handleUpdateScores">
                更新评分
              </van-button>
            </div>
            <div v-for="hot in marketHots" :key="hot.id" class="admin-card">
              <div class="card-row">
                <span class="card-label">平台</span>
                <span class="card-value">{{ hot.platform_name }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">关键词</span>
                <span class="card-value">{{ hot.keyword }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">类型</span>
                <span class="card-value">{{ hot.type }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">优先级提升</span>
                <span class="card-value">{{ hot.priority_boost }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">过期时间</span>
                <span class="card-value">{{ hot.expires_at }}</span>
              </div>
              <div class="card-actions">
                <van-button size="mini" round plain color="#8b5cf6" @click="handleAnalyze(hot.platform_id)">
                  AI 分析
                </van-button>
              </div>
            </div>
            <div v-if="marketHots.length === 0" class="empty-hint">暂无市场热点</div>
          </template>
        </div>
      </van-tab>

      <van-tab title="诊断规则">
        <div class="tab-content">
          <van-loading v-if="rulesLoading" class="section-loading" />
          <template v-else>
            <div v-for="rule in rules" :key="rule.id" class="admin-card">
              <div class="card-row">
                <span class="card-label">名称</span>
                <span class="card-value">{{ rule.name }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">问题类型</span>
                <span class="card-value">{{ rule.problem_type }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">优先级</span>
                <span class="card-value">{{ rule.priority }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">命中</span>
                <span class="card-value">{{ rule.hit_count }}次</span>
              </div>
              <div class="card-row">
                <span class="card-label">准确</span>
                <span class="card-value">{{ rule.accurate_count }}次</span>
              </div>
              <div class="card-row accuracy-row">
                <span class="card-label">准确率</span>
                <van-progress
                  :percentage="rule.accuracy"
                  :color="rule.accuracy >= 80 ? '#07c160' : rule.accuracy >= 50 ? '#ff9900' : '#ff2442'"
                  stroke-width="6"
                  track-color="#f2f2f2"
                  pivot-text=""
                  class="accuracy-bar"
                />
                <span class="accuracy-text">{{ rule.accuracy }}%</span>
              </div>
            </div>
            <div v-if="rules.length === 0" class="empty-hint">暂无诊断规则</div>
          </template>
        </div>
      </van-tab>

      <van-tab title="学习指标">
        <div class="tab-content">
          <van-loading v-if="evolutionLoading" class="section-loading" />
          <template v-else>
            <div class="section-actions">
              <van-button size="small" round color="var(--xh-brand)" @click="handleAdjustWeights">
                手动调整权重
              </van-button>
            </div>
            <div v-for="item in evolutionStats" :key="item.rule_id" class="admin-card">
              <div class="card-row">
                <span class="card-label">规则</span>
                <span class="card-value">{{ item.rule_name }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">当前权重</span>
                <span class="card-value weight-value">{{ item.current_weight }}</span>
              </div>
              <div class="card-row">
                <span class="card-label">准确率</span>
                <van-progress
                  :percentage="item.accuracy"
                  :color="item.accuracy >= 80 ? '#07c160' : item.accuracy >= 50 ? '#ff9900' : '#ff2442'"
                  stroke-width="6"
                  track-color="#f2f2f2"
                  pivot-text=""
                  class="accuracy-bar"
                />
                <span class="accuracy-text">{{ item.accuracy }}%</span>
              </div>
              <div v-if="item.weight_history && item.weight_history.length" class="weight-history">
                <div class="card-label" style="margin-bottom:6px">权重变化</div>
                <div class="history-dots">
                  <span
                    v-for="(w, idx) in item.weight_history"
                    :key="idx"
                    class="history-dot"
                    :style="{ background: getWeightColor(w, item.current_weight) }"
                  ></span>
                </div>
              </div>
            </div>
            <div v-if="evolutionStats.length === 0" class="empty-hint">暂无学习指标</div>
          </template>
        </div>
      </van-tab>
    </van-tabs>

    <van-dialog
      v-model:show="showPathDialog"
      :title="editingPath ? '编辑转化路径' : '新增转化路径'"
      show-cancel-button
      :before-close="onPathDialogClose"
    >
      <div class="dialog-form">
        <van-field v-model="pathForm.intent_id" label="意图ID" placeholder="输入意图ID" />
        <van-field v-model="pathForm.stage" label="阶段" placeholder="public_to_private / private_to_deal / deal_boost" />
        <van-field v-model="pathForm.title" label="标题" placeholder="输入标题" />
        <van-field v-model="pathForm.script_preview" label="话术预览" type="textarea" rows="3" placeholder="输入话术内容" />
      </div>
    </van-dialog>

    <van-dialog
      v-model:show="showHotDialog"
      title="添加市场热点"
      show-cancel-button
      :before-close="onHotDialogClose"
    >
      <div class="dialog-form">
        <van-field v-model="hotForm.platform_id" label="平台ID" placeholder="输入平台ID" />
        <van-field v-model="hotForm.keyword" label="关键词" placeholder="输入关键词" />
        <van-field v-model="hotForm.type" label="类型" placeholder="输入类型" />
        <van-field v-model="hotForm.priority_boost" label="优先级提升" type="digit" placeholder="输入数值" />
        <van-field v-model="hotForm.expires_at" label="过期时间" placeholder="YYYY-MM-DD" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import {
  getAdminStats,
  getContentStructures,
  updateContentStructure,
  getConversionPaths,
  createConversionPath,
  updateConversionPath,
  deleteConversionPath,
  getMarketHots,
  createMarketHot,
  analyzeMarket,
  updateMarketScores,
  getEvolutionStats,
  adjustRuleWeights,
} from '../api/tasks'

const router = useRouter()
const activeTab = ref(0)

const statsLoading = ref(false)
const structuresLoading = ref(false)
const pathsLoading = ref(false)
const hotsLoading = ref(false)
const rulesLoading = ref(false)
const evolutionLoading = ref(false)

const stats = ref<Record<string, number>>({
  total_users: 0,
  total_tasks: 0,
  publish_rate: 0,
  report_rate: 0,
})

interface ContentStructure {
  id: string
  intent_name: string
  platform_name: string
  hook_type: string
  priority: number
  market_score: number
  _editScore: string
}

const structures = ref<ContentStructure[]>([])

interface ConversionPath {
  id: string
  intent_id: string
  intent_name: string
  stage: string
  title: string
  script_preview: string
}

const conversionPaths = ref<ConversionPath[]>([])

const pathsByIntent = computed(() => {
  const grouped: Record<string, ConversionPath[]> = {}
  for (const p of conversionPaths.value) {
    const key = p.intent_name || p.intent_id
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(p)
  }
  return grouped
})

interface MarketHot {
  id: string
  platform_id: string
  platform_name: string
  keyword: string
  type: string
  priority_boost: number
  expires_at: string
}

const marketHots = ref<MarketHot[]>([])

interface Rule {
  id: string
  name: string
  problem_type: string
  priority: number
  hit_count: number
  accurate_count: number
  accuracy: number
}

const rules = ref<Rule[]>([])

interface EvolutionStat {
  rule_id: string
  rule_name: string
  current_weight: number
  accuracy: number
  weight_history: number[]
}

const evolutionStats = ref<EvolutionStat[]>([])

const showPathDialog = ref(false)
const editingPath = ref<ConversionPath | null>(null)
const pathForm = ref({
  intent_id: '',
  stage: '',
  title: '',
  script_preview: '',
})

const showHotDialog = ref(false)
const hotForm = ref({
  platform_id: '',
  keyword: '',
  type: '',
  priority_boost: '',
  expires_at: '',
})

const getStageLabel = (stage: string): string => {
  const map: Record<string, string> = {
    public_to_private: '公域→私域',
    private_to_deal: '私域→成交',
    deal_boost: '成交提升',
  }
  return map[stage] || stage
}

const getStageColor = (stage: string): string => {
  const map: Record<string, string> = {
    public_to_private: '#4A90D9',
    private_to_deal: '#FF8C00',
    deal_boost: '#07c160',
  }
  return map[stage] || '#999'
}

const getStageBg = (stage: string): string => {
  const map: Record<string, string> = {
    public_to_private: '#eff6ff',
    private_to_deal: '#fff7ed',
    deal_boost: '#ecfdf5',
  }
  return map[stage] || '#f5f5f5'
}

const getWeightColor = (w: number, current: number): string => {
  if (w > current) return '#07c160'
  if (w < current) return '#ff2442'
  return '#ff9900'
}

const fetchStats = async () => {
  statsLoading.value = true
  try {
    const res = await getAdminStats()
    stats.value = res.data.stats || res.data
  } catch {
    showToast('加载统计失败')
  } finally {
    statsLoading.value = false
  }
}

const fetchStructures = async () => {
  structuresLoading.value = true
  try {
    const res = await getContentStructures()
    const list = res.data.structures || res.data
    structures.value = list.map((s: any) => ({
      ...s,
      _editScore: String(s.market_score ?? 0),
    }))
  } catch {
    showToast('加载内容结构失败')
  } finally {
    structuresLoading.value = false
  }
}

const saveStructureScore = async (item: ContentStructure) => {
  try {
    await updateContentStructure(item.id, { market_score: Number(item._editScore) })
    showToast({ message: '已保存', icon: 'checked' })
  } catch {
    showToast('保存失败')
  }
}

const fetchPaths = async () => {
  pathsLoading.value = true
  try {
    const res = await getConversionPaths()
    conversionPaths.value = res.data.paths || res.data
  } catch {
    showToast('加载转化路径失败')
  } finally {
    pathsLoading.value = false
  }
}

const openPathDialog = (path?: ConversionPath) => {
  if (path) {
    editingPath.value = path
    pathForm.value = {
      intent_id: path.intent_id,
      stage: path.stage,
      title: path.title,
      script_preview: path.script_preview,
    }
  } else {
    editingPath.value = null
    pathForm.value = { intent_id: '', stage: '', title: '', script_preview: '' }
  }
  showPathDialog.value = true
}

const onPathDialogClose = async (action: string) => {
  if (action !== 'confirm') return true
  try {
    if (editingPath.value) {
      await updateConversionPath(editingPath.value.id, pathForm.value)
    } else {
      await createConversionPath(pathForm.value)
    }
    showToast({ message: '已保存', icon: 'checked' })
    await fetchPaths()
    return true
  } catch {
    showToast('保存失败')
    return false
  }
}

const handleDeletePath = async (id: string) => {
  try {
    await showConfirmDialog({ title: '确认', message: '确定删除该转化路径？' })
  } catch {
    return
  }
  try {
    await deleteConversionPath(id)
    showToast({ message: '已删除', icon: 'checked' })
    await fetchPaths()
  } catch {
    showToast('删除失败')
  }
}

const fetchHots = async () => {
  hotsLoading.value = true
  try {
    const res = await getMarketHots()
    marketHots.value = res.data.hots || res.data
  } catch {
    showToast('加载热点失败')
  } finally {
    hotsLoading.value = false
  }
}

const onHotDialogClose = async (action: string) => {
  if (action !== 'confirm') return true
  try {
    await createMarketHot({
      ...hotForm.value,
      priority_boost: Number(hotForm.value.priority_boost),
    })
    showToast({ message: '已添加', icon: 'checked' })
    await fetchHots()
    return true
  } catch {
    showToast('添加失败')
    return false
  }
}

const handleAnalyze = async (platformId: string) => {
  const toast = showLoadingToast({ message: 'AI 分析中...', forbidClick: true, duration: 0 })
  try {
    await analyzeMarket(platformId)
    showToast({ message: '分析完成', icon: 'checked' })
    await fetchHots()
  } catch {
    showToast('分析失败')
  } finally {
    closeToast()
  }
}

const handleUpdateScores = async () => {
  const toast = showLoadingToast({ message: '更新评分中...', forbidClick: true, duration: 0 })
  try {
    await updateMarketScores()
    showToast({ message: '评分已更新', icon: 'checked' })
    await fetchHots()
  } catch {
    showToast('更新失败')
  } finally {
    closeToast()
  }
}

const fetchRules = async () => {
  rulesLoading.value = true
  try {
    const res = await getEvolutionStats()
    const list = res.data.rules || res.data
    rules.value = list.map((r: any) => ({
      id: r.id,
      name: r.name,
      problem_type: r.problem_type,
      priority: r.priority,
      hit_count: r.hit_count ?? 0,
      accurate_count: r.accurate_count ?? 0,
      accuracy: r.hit_count ? Math.round((r.accurate_count / r.hit_count) * 100) : 0,
    }))
  } catch {
    showToast('加载规则失败')
  } finally {
    rulesLoading.value = false
  }
}

const fetchEvolution = async () => {
  evolutionLoading.value = true
  try {
    const res = await getEvolutionStats()
    evolutionStats.value = res.data.stats || res.data
  } catch {
    showToast('加载学习指标失败')
  } finally {
    evolutionLoading.value = false
  }
}

const handleAdjustWeights = async () => {
  const toast = showLoadingToast({ message: '调整权重中...', forbidClick: true, duration: 0 })
  try {
    await adjustRuleWeights()
    showToast({ message: '权重已调整', icon: 'checked' })
    await fetchEvolution()
  } catch {
    showToast('调整失败')
  } finally {
    closeToast()
  }
}

onMounted(() => {
  fetchStats()
  fetchStructures()
  fetchPaths()
  fetchHots()
  fetchRules()
  fetchEvolution()
})
</script>

<style scoped>
.admin-page {
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

.tab-content {
  padding: 16px;
}

.section-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.stat-card {
  border-radius: var(--radius-card);
  padding: 20px 16px;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.stat-pink {
  background: linear-gradient(135deg, #fff0f2 0%, #ffe4e8 100%);
}

.stat-orange {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
}

.stat-blue {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.stat-green {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--xh-text-primary);
  margin-bottom: 4px;
}

.stat-pink .stat-value {
  color: #ff2442;
}

.stat-orange .stat-value {
  color: #ff8c00;
}

.stat-blue .stat-value {
  color: #4a90d9;
}

.stat-green .stat-value {
  color: #07c160;
}

.stat-label {
  font-size: 12px;
  color: var(--xh-text-tertiary);
}

.admin-card {
  background: var(--xh-bg-primary);
  border-radius: var(--radius-card);
  padding: 16px;
  margin-bottom: 10px;
  box-shadow: var(--shadow-card);
}

.card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.card-label {
  font-size: 13px;
  color: var(--xh-text-tertiary);
  flex-shrink: 0;
}

.card-value {
  font-size: 13px;
  color: var(--xh-text-primary);
  font-weight: 500;
  text-align: right;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.script-preview {
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.inline-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-input {
  width: 80px;
  padding: 0;
  background: var(--xh-bg-secondary);
  border-radius: var(--radius-input);
}

.score-input :deep(.van-field__control) {
  text-align: center;
  font-size: 14px;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--xh-border);
}

.stage-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-tag);
  font-size: 12px;
  font-weight: 500;
}

.section-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.intent-group {
  margin-bottom: 16px;
}

.group-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--xh-text-primary);
  margin-bottom: 8px;
  padding-left: 4px;
}

.accuracy-row {
  gap: 8px;
}

.accuracy-bar {
  flex: 1;
}

.accuracy-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--xh-text-primary);
  min-width: 36px;
  text-align: right;
}

.weight-value {
  color: #ff9900;
  font-weight: 700;
}

.weight-history {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--xh-border);
}

.history-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.history-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.empty-hint {
  text-align: center;
  color: var(--xh-text-tertiary);
  font-size: 14px;
  padding: 40px 0;
}

.dialog-form {
  padding: 16px;
}

.dialog-form .van-field {
  margin-bottom: 8px;
  background: var(--xh-bg-secondary);
  border-radius: var(--radius-input);
}
</style>
