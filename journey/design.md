# Intent Money OS - 项目设计快照

## 项目概述
意图选择式赚钱系统 MVP，面向袜子分销商的"一键赚钱执行系统"。

## 核心闭环
选择意图 → 获取唯一任务 → 用户发布 → 数据自动抓取/手动回传 → 规则+AI诊断+情感分析 → 生成下一条优化任务

## 技术栈
- 前端：Vue 3 + TypeScript + Vant 4 + Pinia + Vite
- 后端：FastAPI (Python 3.11+) + SQLAlchemy + Alembic
- 数据库：SQLite (aiosqlite 异步驱动)
- AI：DeepSeek V4 Flash via OpenRouter API（openai SDK AsyncOpenAI）
- 部署：Docker Compose (FastAPI + Nginx，无独立数据库容器)
- 包管理：uv (Python), pnpm (前端)
- 端口：后端 9090，前端 5173/5174

## MVP 范围
- 4 个意图全部开放（引流拿客户/成交赚钱/裂变招募分销/IP长期增长）
- 抖音 + 小红书平台
- 数据自动抓取（抖音/小红书 httpx 异步爬虫）+ 手动回填降级
- 规则诊断 + AI 深度诊断 + 评论情感分析
- 自动发布（social-auto-upload subprocess 调用）+ 手动发布降级
- H5 单页应用（微信内嵌 / 浏览器）

## 关键设计决策
1. 单体架构，不引入微服务/消息队列
2. 匿名用户可完成完整闭环，JWT 7 天有效期
3. AI 负责文案填充 + 爆款结构提取 + 情感分析辅助诊断
4. AI 失败时使用 fallback_content 兜底
5. 换一条每天限 1 次
6. 任务状态机：PENDING → PUBLISHED → REPORTED → DIAGNOSED → (下一条)
7. 所有新功能默认关闭或降级：AUTO_PUBLISH_ENABLED/SMS_ENABLED 默认 False
8. 爬虫失败降级到手动录入，发布失败降级到手动发布，情感分析失败返回 neutral
9. 爆款结构提取需管理员审核后才写入 content_structures 表
10. RBAC 权限：admin/user 两级角色，admin API 受 require_admin 保护

## 数据模型
13 张核心表：users, user_sessions, intents, platforms, content_structures, content_tasks, performance_reports, diagnosis_results, optimization_rules, market_hots, user_events, extracted_structures

新增字段：
- users.role: String(20), 默认 "user"
- market_hots.comment_sentiment: JSON, 评论情感分析结果

## 平台数据抓取架构
- BasePlatformScraper 抽象基类（search/get_detail/get_comments/check_health）
- DouyinScraper: httpx 异步请求抖音 Web API，Cookie 认证
- XhsScraper: httpx 异步请求小红书 Web API，Cookie 认证
- 定时任务：每日自动抓取爆款数据写入 market_hots 表
- 降级策略：全链路 try/except，失败返回空列表/None，记录日志

## 发布确认架构
- auto_publisher.py: subprocess 调用 social-auto-upload
- cookie_manager.py: Cookie 文件存储在 backend/cookies/ 目录，7天过期
- 任务详情页主入口为“确认已发放”：用户复制话术并手动发布到平台后，点击该按钮调用 `POST /api/v1/tasks/{id}/publish`，任务状态进入 `PUBLISHED`
- 自动发布作为次级入口保留：优先尝试自动发布，失败后降级到手动确认

## 爆款结构提取架构
- structure_extractor.py: AI（DeepSeek）分析爆款视频/笔记内容结构
- extracted_structures 表：存储待审核的提取结构（pending/approved/rejected）
- 管理员审核通过后写入 content_structures 表

## 评论情感分析架构
- sentiment_service.py: SnowNLP 轻量级中文情感分析
- 评分规则：score >= 0.6 → positive, 0.4~0.6 → neutral, < 0.4 → negative
- 集成到数据抓取流程：抓取评论 → 批量情感分析 → 结果存入 market_hots.comment_sentiment
- 诊断集成：正面 > 60% → 结构有效，负面 > 40% → 需优化

## 用户行为追踪架构
- user_events 表：event_type/page/duration/metadata_json
- 前端 tracker.js：session_id 自动生成，5秒批量上报，sendBeacon 优先
- 埋点事件：page_view, intent_selected, content_copied, publish_clicked

## 短信验证码架构
- sms_service.py: 阿里云短信 API（httpx 异步调用）
- 内存验证码缓存，5分钟过期
- SMS_ENABLED=False 时使用固定验证码 123456（向后兼容）

## 项目目录
代码位于 `intent-money/` 目录下，结构为 frontend / backend / docker

## 当前阶段
Phase 2 - 开源集成与核心闭环打通

## UI 设计系统（2026-05-21 更新）

### 视觉风格
小红书风格：温暖、生活化、杂志感的移动内容创作工具

### 设计 Token
- 品牌色：`#FF2442`（小红书红）
- 背景色：纯白 `#FFFFFF` / 次级 `#F7F7F7` / 输入框 `#F2F2F2`
- 文字色：主 `#333333` / 次 `#666666` / 辅助 `#999999`
- 圆角：卡片 16px / 按钮 24px（全圆角胶囊）/ 输入框 12px
- 阴影：`0 2px 12px rgba(0,0,0,0.04)` / `0 4px 20px rgba(0,0,0,0.08)`
- 字体：`-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Helvetica Neue', sans-serif`

### 页面结构
- 意图选择页：纯白底 + 左对齐标题 + 2 列竖版卡片网格（stagger 入场动画）
- 任务详情页：自定义导航栏 + 卡片化内容区（左侧彩色竖条）+ 悬浮底部操作区（一键发布按钮）
- 数据报告页：任务摘要卡片 + 表单卡片 + 诊断结果卡片（图标 + 卡片式展示）

### 动效规范
- 页面过渡：opacity 0→1 + translateY(20px→0)，300ms ease-out
- 卡片交互：hover translateY(-2px) / active scale(0.98)

## 新增 .env 配置项
```
DOUYIN_COOKIE=         # 抖音 Cookie
XHS_COOKIE=            # 小红书 Cookie
SCRAPER_TIMEOUT=30     # 抓取超时
SCRAPER_ENABLED=true   # 是否启用抓取
AUTO_PUBLISH_ENABLED=false  # 自动发布（默认关闭）
SOCIAL_AUTO_UPLOAD_PATH=   # social-auto-upload 路径
COOKIE_DIR=cookies     # Cookie 存储目录
COOKIE_EXPIRE_DAYS=7   # Cookie 过期天数
SMS_ENABLED=false      # 短信服务（默认关闭）
SMS_GATEWAY=           # aliyun/tencent/huawei
SMS_ACCESS_KEY=
SMS_SECRET_KEY=
SMS_SIGN_NAME=
SMS_TEMPLATE_CODE=
SENTIMENT_ENABLED=true # 情感分析开关
```

## 风险与约束
- 平台反爬导致抓取不稳定 → 全链路降级策略（手动录入兜底）
- social-auto-upload 依赖 Playwright 模拟操作 → 平台 UI 变更可能失效
- AI 内容质量不稳定 → 校验 + 兜底
- 结构库质量依赖运营 → 需提前准备 20+ 模板 + 爆款提取审核机制
- Cookie 有效期有限 → 7天过期检测 + 手动刷新机制
