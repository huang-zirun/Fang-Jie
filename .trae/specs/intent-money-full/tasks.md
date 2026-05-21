# Tasks

## 第 1 阶段：全意图开放 + 平台选择

- [x] Task 1: 开放全部 4 个意图并补充种子数据
  - [x] SubTask 1.1: 修改 `seed.py` 将"成交赚钱""裂变招募分销""IP长期增长"的 `is_active` 设为 True
  - [x] SubTask 1.2: 为"成交赚钱"意图创建 5+ 内容结构模板（抖音 3+小红书 2+），覆盖促单转化场景
  - [x] SubTask 1.3: 为"裂变招募分销"意图创建 5+ 内容结构模板（抖音 3+小红书 2+），覆盖招募分销场景
  - [x] SubTask 1.4: 为"IP长期增长"意图创建 5+ 内容结构模板（抖音 3+小红书 2+），覆盖品牌建设场景
  - [x] SubTask 1.5: 为 3 个新意图各创建 3+ 条诊断规则（optimization_rules 种子数据）
  - [x] SubTask 1.6: 删除旧数据库文件使种子数据重新初始化，验证 4 个意图全部可用

- [x] Task 2: 平台选择步骤
  - [x] SubTask 2.1: 新增 `frontend/src/views/PlatformSelect.vue` 页面，展示抖音/小红书选择卡片
  - [x] SubTask 2.2: 修改路由，意图选择后跳转到平台选择页（`/platform/:intentId`）
  - [x] SubTask 2.3: 修改 `IntentSelect.vue`，移除硬编码的 `DOUYIN_ID`，选择意图后跳转到平台选择页
  - [x] SubTask 2.4: 平台选择页选择后携带 intentId + platformId 调用 createTask API

- [x] Task 3: 首屏 UI 升级
  - [x] SubTask 3.1: 修改 `IntentSelect.vue` 标题为"今天你想通过什么方式赚钱？"
  - [x] SubTask 3.2: 移除灰显逻辑，4 个意图全部可点击
  - [x] SubTask 3.3: 选择意图后展示系统反馈语"我已基于当前平台+实时同类爆款数据，为你生成了今天最优赚钱动作方案"（1.5s 后自动跳转）
  - [x] SubTask 3.4: 优化意图卡片样式，为每个意图增加差异化视觉标识（图标/颜色）

## 第 2 阶段：爆款结构引擎 + 转化路径引擎

- [x] Task 4: 爆款结构引擎扩展
  - [x] SubTask 4.1: 新增 `content_structures.market_score` 字段（Float，默认 0），用于市场热度评分
  - [x] SubTask 4.2: 修改 `match_content_structure` 函数，排序逻辑加入 `priority * 0.6 + market_score * 0.4` 权重计算
  - [x] SubTask 4.3: 新增 `app/api/v1/admin.py` 中的结构模板批量导入 API
  - [x] SubTask 4.4: 补充内容结构种子数据至 40+ 模板（4 意图×2 平台×5+模板）
  - [x] SubTask 4.5: 修改 AI Prompt 构造，为不同意图使用差异化的 Prompt 模板（引流/成交/裂变/IP 各一套）

- [x] Task 5: 转化路径引擎
  - [x] SubTask 5.1: 新增 `app/models/conversion_path.py` 数据模型
  - [x] SubTask 5.2: 新增 `app/schemas/conversion_path.py` 请求/响应 schema
  - [x] SubTask 5.3: 新增 `app/api/v1/conversion_paths.py` CRUD API
  - [x] SubTask 5.4: 新增 `app/services/conversion_service.py`
  - [x] SubTask 5.5: 修改 `task_service.py` 的 `generate_task`，注入转化路径话术
  - [x] SubTask 5.6: 为 4 个意图创建转化路径种子数据（24 条）
  - [x] SubTask 5.7: 修改 AI Prompt，注入转化路径话术参考

## 第 3 阶段：实时数据引擎 + 学习进化引擎

- [x] Task 6: 实时数据引擎
  - [x] SubTask 6.1: 新增 `app/models/market_hot.py` 数据模型
  - [x] SubTask 6.2: 新增 `app/schemas/market_hot.py` 请求/响应 schema
  - [x] SubTask 6.3: 新增 `app/api/v1/market.py` API
  - [x] SubTask 6.4: 新增 `app/services/market_service.py`
  - [x] SubTask 6.5: 修改 `match_content_structure`，市场热点动态提升 market_score
  - [x] SubTask 6.6: 新增定时任务：每日自动触发市场趋势分析

- [x] Task 7: 学习进化引擎
  - [x] SubTask 7.1: 修改 `diagnosis_service.py`，AI 增强诊断
  - [x] SubTask 7.2: 新增 `diagnosis_results.ai_analysis` 字段
  - [x] SubTask 7.3: 新增 `diagnosis_results.rule_confidence` 字段
  - [x] SubTask 7.4: 新增 `optimization_rules.hit_count` 和 `accuracy_count` 字段
  - [x] SubTask 7.5: 新增 `app/services/evolution_service.py`
  - [x] SubTask 7.6: 修改数据回传流程，记录规则命中和准确性
  - [x] SubTask 7.7: 新增定时任务：每周自动调整规则权重

## 第 4 阶段：前端完善 + 运营后台

- [x] Task 8: 任务历史页面
  - [x] SubTask 8.1: 新增 `GET /api/v1/tasks/history` API
  - [x] SubTask 8.2: 新增 `frontend/src/views/TaskHistory.vue` 页面
  - [x] SubTask 8.3: 历史任务卡片显示意图/平台/状态/关键指标
  - [x] SubTask 8.4: 支持按意图和状态筛选
  - [x] SubTask 8.5: 新增路由 `/history`，增加入口

- [x] Task 9: 任务详情页升级
  - [x] SubTask 9.1: 按意图差异化展示转化话术
  - [x] SubTask 9.2: 诊断结果展示 AI 分析内容
  - [x] SubTask 9.3: 优化"获取下一条任务"流程，展示优化说明

- [x] Task 10: 运营后台升级
  - [x] SubTask 10.1: 新增转化路径管理
  - [x] SubTask 10.2: 新增市场热点管理
  - [x] SubTask 10.3: 新增 AI 诊断日志查看
  - [x] SubTask 10.4: 新增系统学习指标面板
  - [x] SubTask 10.5: 新增内容结构市场评分管理

## 第 5 阶段：集成测试 + 记忆系统更新

- [x] Task 11: 集成测试
  - [x] SubTask 11.1: 测试 4 个意图 API 可用性
  - [x] SubTask 11.2: 测试转化路径话术注入
  - [x] SubTask 11.3: 测试市场热点 API
  - [x] SubTask 11.4: 测试任务创建完整流程
  - [x] SubTask 11.5: 测试后端启动和种子数据初始化
  - [x] SubTask 11.6: 测试前端构建通过

- [x] Task 12: 记忆系统更新
  - [x] SubTask 12.1: 创建 `journey/design.md`
  - [x] SubTask 12.2: 创建 `journey/logs/2026-05-21-full-development.md`
  - [x] SubTask 12.3: 更新 `project_memory.md`

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 1
- Task 5 depends on Task 4
- Task 6 depends on Task 4
- Task 7 depends on Task 6
- Task 8 depends on Task 1, Task 2
- Task 9 depends on Task 5, Task 7
- Task 10 depends on Task 5, Task 6, Task 7
- Task 11 depends on Task 8, Task 9, Task 10
- Task 12 depends on Task 11
