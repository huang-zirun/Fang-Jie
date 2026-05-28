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
- 浏览器自动化：websockets (CDP 协议连接已登录 Chrome)

## 启动方式

### 一键启动（推荐）

```bash
cd intent-money
uv run python server.py
```

`server.py` 同时启动后端（FastAPI + uvicorn）和前端（Vite），Ctrl+C 同时停止。

后端启动参数：`--host 127.0.0.1 --port 9090`

> **注意**：默认不启用 `--reload`，因为 SQLite 数据库文件在工作目录中，频繁写入会触发 reload 导致服务不稳定。如需开发时热重载，使用 `--reload` 参数。

### 手动分步启动

```bash
# 1. 启动后端（生产模式，稳定运行）
cd intent-money/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 9090

# 2. 启动后端（开发模式，带热重载）
cd intent-money/backend
uv run uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 9090

# 3. 启动前端
cd intent-money/frontend
npm run dev
```

### 验证

```bash
# CDP 健康检查
curl http://127.0.0.1:9090/api/v1/scraper/health
# 期望：{"douyin": {"healthy": true, "cdp": true}, "xhs": {"healthy": true, "cdp": true}}

# 小红书搜索
curl -X POST "http://127.0.0.1:9090/api/v1/scraper/xhs/search?keyword=袜子&limit=5"

# 抖音搜索
curl -X POST "http://127.0.0.1:9090/api/v1/scraper/douyin/search?keyword=袜子&limit=5"
```

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
- platforms.description: String(200), 平台描述文案（前端展示用）

## 平台数据抓取架构
- BasePlatformScraper 抽象基类（search/get_detail/get_comments/check_health）
- **CDP 模式**（默认）：通过 Chrome DevTools Protocol 连接已登录的 Chrome 浏览器抓取数据
  - `CdpBrowser`：管理 CDP WebSocket 连接、页面导航、JS 执行
  - `CdpXhsScraper`：小红书 CDP 爬虫，导航搜索页后用 CSS 选择器提取笔记数据
  - `CdpDouyinScraper`：抖音 CDP 爬虫，导航搜索页后用正则解析视频数据
  - 开关：`CDP_ENABLED=true` 启用，`CDP_ENABLED=false` 降级到原始 API 爬虫
  - Chrome 启动参数：`--remote-debugging-port=9222 --remote-debugging-address=127.0.0.1`
- **原始 API 模式**（降级）：httpx 异步请求平台 Web API，Cookie 认证
  - DouyinScraper / XhsScraper：需要手动配置 DOUYIN_COOKIE / XHS_COOKIE
- 定时任务：每日自动抓取爆款数据写入 market_hots 表
- 降级策略：全链路 try/except，失败返回空列表/None，记录日志

## 发布确认架构
- auto_publisher.py: CDP 优先 → sau CLI 降级 → 手动确认（CDP 使用 DOM.setFileInputFiles 真正上传文件，60秒超时自动降级）
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

## CDP 驱动内容生成架构

### 设计目标
将 CDP 抓取的市场热门数据直接注入 AI 内容生成流程，使生成的内容更贴近当前市场热点。

### 数据流
```
CDP 抓取 → market_hots 表 → _get_market_insights() → AI Prompt → 生成内容
```

### 关键组件
- `task_service._get_market_insights()`: 聚合 market_hots 分析数据
- `ai_service._build_prompt()`: 在 prompt 中注入市场热门参考
- `market_analyzer.py` (可选): 分析热门内容提取创作灵感

### 数据格式
market_insights 结构：
- hot_titles: 热门标题列表
- hot_tags: 热门标签
- emotional_patterns: 情绪转换模式
- high_engagement_hooks: 高互动钩子
- sentiment_summary: 评论情感分析摘要

### 降级策略
当 market_insights 为空时，保持原有模板驱动生成逻辑。
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
- 2026-05-25：新增 CDP 浏览器自动化抓取服务，替代裸 API 爬虫
  - 新增 `cdp_browser.py` / `cdp_xhs_scraper.py` / `cdp_douyin_scraper.py`
  - 通过 Chrome DevTools Protocol 连接已登录 Chrome 抓取数据
  - `CDP_ENABLED` 开关控制，默认启用，可降级到原始 API 模式
- 2026-05-25：修复后端 WinError 10013 启动失败
  - 根因：`--reload` 监听整个 `backend/` 目录（含 `.venv`），Windows 上文件句柄与 socket bind 竞争触发 10013
  - 修复：添加 `--reload-dir app` 限制监听范围
  - 修复：添加端口探针（`socket.create_connection` 轮询 15 秒），端口真正监听后才报告"已启动"

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
DOUYIN_COOKIE=         # 抖音 Cookie（CDP 模式下不需要）
XHS_COOKIE=            # 小红书 Cookie（CDP 模式下不需要）
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

# CDP (Chrome DevTools Protocol) 配置
CDP_ENABLED=true           # 是否使用 CDP 模式（连接已登录 Chrome 抓取数据）
CDP_DEBUG_HOST=127.0.0.1   # Chrome 调试地址
CDP_DEBUG_PORT=9222        # Chrome 调试端口

# 开发模式配置
DEV_MODE=false             # 开发模式开关，开启后无限换条（生产环境保持 false）
```

## 风险与约束
- CDP 模式依赖 Chrome 运行且已登录 → Chrome 未启动或未登录时降级到原始 API 爬虫（需手动配置 Cookie）
- 平台反爬导致抓取不稳定 → 全链路降级策略（手动录入兜底）
- social-auto-upload 依赖 Playwright 模拟操作 → 平台 UI 变更可能失效
- AI 内容质量不稳定 → 校验 + 兜底
- 结构库质量依赖运营 → 需提前准备 20+ 模板 + 爆款提取审核机制
- Cookie 有效期有限 → 7天过期检测 + 手动刷新机制（仅 API 模式需要）

## 2026-05-26 下一条优化任务契约
- `POST /api/v1/tasks/{task_id}/next` 使用 JSON body，不再依赖必填 query 参数。
- body 字段可选：`platform_id`、`task_type`；缺省时后端沿用原任务的平台和任务类型。
- `TaskOut` 输出 `intent_id`、`platform_id`、`task_type`，前端不得硬编码平台 ID。

## 2026-05-26 AI 内容生成策略更新
- 内容生成从“分销强转化话术”改为“平台原生内容优先，低压转化承接”。
- 抖音生成重点：前3秒停留、视频动作、口播节奏、画面变化、评论互动。
- 小红书生成重点：封面点击、真实笔记感、图文信息增量、收藏价值、场景/搭配/清单。
- 评论区话术不再强制私信、链接、扣1、小黄车，而是以问题、场景、清单、搭配建议承接。
- 校验层新增强营销短语拦截，降低“秒发链接/私信暗号/限时逼单”类输出。
- AI 失败或旧结构 fallback 触发时，需先通过同一校验；不合格则使用安全兜底模板。
## 2026-05-26 Operations dashboard data contract
- The current-user operations dashboard must not call admin-only stats during anonymous startup.
- Dashboard overview endpoint: `GET /api/v1/tasks/overview`.
- Auth: any authenticated current user via `get_current_user`.
- Response fields: `today_tasks`, `today_published`, `today_pending`, `today_swapped`, `total_problems`, `intent_distribution`, `problem_stats`.
- Admin-only operational configuration remains under `/api/v1/admin/*` and keeps `require_admin`.

## 2026-05-27 小红书文案语境优化
- 任务详情页文案根据平台动态切换：
  - "分镜脚本" → 小红书显示"图文脚本"
  - "口播文案" → 小红书显示"笔记正文"
  - 提示语"标题和文案已可复制" → 小红书显示"标题和正文已可复制"
- 数据回填页文案根据平台动态切换：
  - "播放量" → 小红书显示"阅读量"
- 实现方式：前端 Vue computed 属性根据 `platform_name` 是否包含"小红书"动态返回对应文案
- 修改文件：`frontend/src/views/TaskDetail.vue`, `frontend/src/views/DataReport.vue`
