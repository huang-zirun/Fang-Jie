# Intent Money OS - 设计文档

## 项目定位

**意图选择式赚钱系统（Intent-based Money OS）**

核心逻辑：用户不思考，只选目标。系统接管一切复杂度。

> 前台 = 一键赚钱按钮
> 后台 = 顶级运营团队的大脑

## 技术架构

### 后端
- FastAPI + SQLAlchemy + aiosqlite (SQLite)
- AI: DeepSeek V4 Flash via OpenRouter (AsyncOpenAI)
- 端口: 9090
- 数据库文件: `backend/intent_money.db`

### 前端
- Vue 3 + TypeScript + Vant 4 + Pinia + Vue Router
- 端口: 5173 (dev)
- Vite proxy → http://127.0.0.1:9090

### 部署
- Docker Compose: FastAPI + Frontend + Nginx
- 一键启动: `python server.py`

## 四大引擎

### 1. 爆款结构引擎
- 内容结构库: 20+ 模板覆盖 4 意图×2 平台
- 结构匹配: `priority * 0.6 + market_score * 0.4` 加权排序
- AI Prompt 差异化: 每个意图有独立的任务描述/目标人群/why_it_works 模板
- 转化路径注入: 生成任务时注入对应意图的转化路径话术

### 2. 实时数据引擎
- 市场热点管理: 运营录入热点关键词+AI 分析趋势
- market_score 动态提升: 热点匹配的结构在内存中临时提升 market_score
- 定时任务: 每 24h 自动分析抖音/小红书市场趋势
- 手动触发: POST /api/v1/market/update-scores

### 3. 转化路径引擎
- 三段转化链: 公域→私域 / 私域→成交 / 成交提升
- 每个意图 3 段×2 条 = 24 条种子话术
- 生成任务时自动注入转化路径话术到 AI Prompt
- 任务详情页按意图差异化展示转化话术

### 4. 学习进化引擎
- AI 增强诊断: 规则匹配 + AI 深度分析
- 规则命中统计: hit_count / accuracy_count
- 自动权重调整: 准确率 > 0.7 → priority += 5; < 0.4 → priority -= 5
- 定时任务: 每 7 天自动调整规则权重

## 用户流程

```
选择意图(4选1) → 系统反馈语(1.5s) → 选择平台(抖音/小红书) → 生成任务 → 执行发布 → 数据回传 → AI 诊断 → 优化下一条 → 循环
```

## 数据模型

### 核心表
- `intents` - 4 个赚钱意图
- `platforms` - 抖音/小红书
- `content_structures` - 内容结构模板 (含 market_score)
- `conversion_paths` - 转化路径话术 (stage: public_to_private/private_to_deal/deal_boost)
- `optimization_rules` - 诊断规则 (含 hit_count, accuracy_count, intent_id)
- `content_tasks` - 用户任务
- `diagnosis_results` - 诊断结果 (含 ai_analysis, rule_confidence)
- `market_hots` - 市场热点数据
- `users` / `sessions` - 用户和会话

## 关键设计决策

1. **SQLite 而非 PostgreSQL**: 简化部署，使用 aiosqlite 异步驱动
2. **内存临时 market_score**: 热点匹配时只在内存中提升，不污染数据库
3. **AI 兜底策略**: AI 调用失败时使用规则诊断结果作为兜底
4. **规则意图绑定**: optimization_rules 新增 intent_id 字段，支持意图专属规则
5. **转化路径 JSON 存储**: scripts 字段用 JSON 存储 opener/guide/close 三段话术
6. **asyncio.create_task 定时任务**: 不引入第三方库，使用原生 asyncio

## 约束

- 后端端口: 9090
- 前端 Vite proxy: http://127.0.0.1:9090
- AI 模型: deepseek/deepseek-chat-v3-0324:free (via OpenRouter)
- 禁用词: 最便宜、全网最低、月入过万等
