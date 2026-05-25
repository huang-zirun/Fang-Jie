# 2026-05-22 开源替代方案调研与集成

## 背景
需求对照分析文档显示 142 项需求中 44 项(31%)完全未实现，核心缺口集中在：实时数据引擎(0/10)、自动闭环(数据抓取+自动发布)、护城河验证机制。通过复用 GitHub 上成熟的开源项目，大幅降低从零实现的成本。

## 调研过程

### 抖音/小红书数据抓取
| 项目 | Stars | 可复用度 | 决策 |
|------|-------|---------|------|
| Evil0ctal/Douyin_TikTok_Download_API | 18k | ⭐⭐⭐⭐ | FastAPI 原生，但功能偏下载而非数据采集 |
| JoeanAmier/TikTokDownloader | 14.5k | ⭐⭐⭐⭐ | 功能最全面（评论/热榜/搜索），但代码耦合重 |
| reajason/xhs | 活跃 | ⭐⭐⭐⭐ | pip install xhs 最轻量 |
| **最终决策** | - | - | 自建 httpx 异步爬虫，参考上述项目的 API 接口和签名逻辑 |

### 自动发布
| 项目 | Stars | 可复用度 | 决策 |
|------|-------|---------|------|
| dreammis/social-auto-upload | 11.2k | ⭐⭐⭐⭐⭐ | 唯一成熟方案，Playwright 模拟操作 |
| **最终决策** | - | - | subprocess 调用 social-auto-upload，隔离 Playwright 进程 |

### 评论情感分析
| 项目 | 可复用度 | 决策 |
|------|---------|------|
| SnowNLP | ⭐⭐⭐⭐⭐ | **采用** - pip install snownlp，零配置，适合短文本 |
| PaddleNLP | ⭐⭐⭐ | 太重，后续可升级 |

### 爆款结构提取
| 项目 | 可复用度 | 决策 |
|------|---------|------|
| viral-video-analyzer | ⭐⭐⭐⭐⭐ | FastAPI 原生，但项目较新 |
| **最终决策** | - | 自建 AI 分析（DeepSeek），先获取平台元数据再交给 AI 拆解结构 |

### 权限控制
| 项目 | 可复用度 | 决策 |
|------|---------|------|
| FastapiAdmin | ⭐⭐⭐ | 需 MySQL+Redis，与 SQLite 不兼容 |
| **最终决策** | - | 自建轻量 RBAC（admin/user 两级，JWT + require_admin 依赖注入） |

### 短信验证码
| 项目 | 可复用度 | 决策 |
|------|---------|------|
| senweaver-sms | ⭐⭐⭐⭐⭐ | 多服务商聚合 SDK |
| **最终决策** | - | 自建阿里云短信服务（httpx 异步调用），SMS_ENABLED 默认关闭 |

### 用户行为追踪
| 项目 | 可复用度 | 决策 |
|------|---------|------|
| PostHog | ⭐⭐ | 需 PostgreSQL+Redis，太重 |
| **最终决策** | - | 自建轻量方案（user_events 表 + 前端 tracker.js） |

## 实施内容

### P0 核心闭环打通（4 个任务）

1. **抖音数据抓取模块**
   - 新建 `platform_scraper/base_scraper.py` - 抽象基类
   - 新建 `platform_scraper/douyin_scraper.py` - httpx 异步爬虫
   - 新建 `api/v1/scraper.py` - API 端点（搜索/评论/健康检查）
   - 修改 `market_service.py` - 新增 `scrape_and_save_hot_videos()`
   - 修改 `main.py` - 新增每日定时抓取任务

2. **小红书数据抓取模块**
   - 新建 `platform_scraper/xhs_scraper.py` - httpx 异步爬虫
   - 新建 `api/v1/scraper_xhs.py` - 小红书 API 端点
   - 修改 `market_service.py` - 新增 `scrape_and_save_xhs_notes()`

3. **自动发布服务**
   - 新建 `services/auto_publisher.py` - subprocess 调用 social-auto-upload
   - 新建 `services/cookie_manager.py` - Cookie 文件管理（7天过期）
   - 新建 `api/v1/publisher.py` - 发布 API（自动发布/Cookie 上传/Cookie 状态）
   - 修改 `TaskDetail.vue` - "我已发布"→"一键发布"（自动发布优先，失败降级手动）

4. **爆款结构自动提取**
   - 新建 `services/structure_extractor.py` - AI 分析爆款结构
   - 新建 `models/extracted_structure.py` - 待审核提取结构表
   - 新建 `api/v1/structure_extractor.py` - 管理员 API（提取/查看/审核）
   - 审核通过后自动写入 content_structures 表

### P1 进化引擎增强（2 个任务）

5. **评论情感分析**
   - 新建 `services/sentiment_service.py` - SnowNLP 情感分析
   - 修改 `market_hot.py` - 新增 `comment_sentiment` JSON 字段
   - 修改 `market_service.py` - 抓取流程集成情感分析
   - 修改 `diagnosis_service.py` - 情感数据纳入诊断依据
   - 新增 `GET /api/v1/admin/sentiment-summary` API

6. **用户行为事件追踪**
   - 新建 `models/user_event.py` - UserEvent 模型
   - 新建 `api/v1/events.py` - 批量上报 + 统计 API
   - 新建 `frontend/src/utils/tracker.js` - 轻量事件追踪器
   - 修改 `App.vue` - tracker 初始化 + 页面切换追踪
   - 修改 `IntentSelect.vue` - intent_selected 事件
   - 修改 `TaskDetail.vue` - content_copied / publish_clicked 事件

### P2 安全与体验完善（2 个任务）

7. **RBAC 权限控制**
   - 修改 `User` 模型 - 新增 `role` 字段（admin/user）
   - 修改 `deps.py` - 新增 `require_admin` 依赖
   - 修改 `admin.py` - 所有 admin 路由受 require_admin 保护
   - 新增 `POST /auth/set-admin` - 设置管理员（需 SECRET_KEY 验证）

8. **短信验证码**
   - 新建 `services/sms_service.py` - 阿里云短信 + 内存验证码缓存
   - 修改 `auth.py` - 新增 `POST /auth/send-code`，login 使用 sms_service.verify_code
   - SMS_ENABLED=False 时使用固定验证码 123456（向后兼容）

## 修复的问题
- `api/v1/scraper.py` 缺少抖音端点和健康检查 → 补充完整
- `api/v1/router.py` 缺少 publisher_router 注册 → 补充注册
- `api/v1/events.py` 未使用的 HTTPException import → 移除
- `models/optimization_rule.py` 未使用的 relationship import → 移除
- `api/v1/tasks.py` 未使用的 platform_row 变量 → 移除赋值

## 验证结果
- ✅ `ruff check app/` - All checks passed
- ✅ SnowNLP 功能测试：`analyze_sentiment('这个产品真的很好用')` → `{'score': 0.838, 'label': 'positive'}`
- ✅ 所有新增文件存在且内容合理
- ✅ 所有路由正确注册

## 新增 API 端点（16 个）
- `/api/v1/scraper/douyin/search` POST
- `/api/v1/scraper/douyin/comments/{video_id}` POST
- `/api/v1/scraper/xhs/search` POST
- `/api/v1/scraper/xhs/comments/{note_id}` POST
- `/api/v1/scraper/health` GET
- `/api/v1/publish/{task_id}/auto` POST
- `/api/v1/publish/cookie` POST
- `/api/v1/publish/cookie/{platform}` GET
- `/api/v1/admin/extract-structure` POST
- `/api/v1/admin/extracted-structures` GET
- `/api/v1/admin/extracted-structures/{id}/approve` POST
- `/api/v1/admin/sentiment-summary` GET
- `/api/v1/events` POST
- `/api/v1/events/stats` GET
- `/api/v1/auth/send-code` POST
- `/api/v1/auth/set-admin` POST

## 新增数据表（2 张）
- `user_events` - 用户行为事件
- `extracted_structures` - 待审核的爆款结构提取

## 新增配置项（14 个）
DOUYIN_COOKIE, XHS_COOKIE, SCRAPER_TIMEOUT, SCRAPER_ENABLED, AUTO_PUBLISH_ENABLED, SOCIAL_AUTO_UPLOAD_PATH, COOKIE_DIR, COOKIE_EXPIRE_DAYS, SMS_ENABLED, SMS_GATEWAY, SMS_ACCESS_KEY, SMS_SECRET_KEY, SMS_SIGN_NAME, SMS_TEMPLATE_CODE, SENTIMENT_ENABLED

## 后续待办
- 实际对接抖音/小红书 Cookie 后测试抓取功能
- 安装 social-auto-upload 后测试自动发布
- 配置阿里云短信后测试真实验证码
- 运行 Alembic 迁移确保数据库 schema 更新
