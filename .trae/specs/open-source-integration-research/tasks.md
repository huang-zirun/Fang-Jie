# Tasks

## 第 1 阶段：P0 核心闭环打通

- [x] Task 1: 集成抖音数据抓取模块
  - [x] SubTask 1.1: 调研 JoeanAmier/TikTokDownloader 数据采集模块的API接口，确定可复用的核心类和方法
  - [x] SubTask 1.2: 在 backend/app/services/ 新增 platform_scraper/douyin_scraper.py，封装抖音数据抓取逻辑
  - [x] SubTask 1.3: 新增 backend/app/api/v1/scraper.py API，提供手动触发抓取和查询抓取结果的接口
  - [x] SubTask 1.4: 修改 market_service.py，抓取结果自动写入 market_hots 表并更新 market_score
  - [x] SubTask 1.5: 新增定时任务：每日自动抓取抖音爆款数据
  - [x] SubTask 1.6: 实现抓取失败降级策略（异常捕获+日志+回退手动模式）

- [x] Task 2: 集成小红书数据抓取模块
  - [x] SubTask 2.1: pip install xhs，调研 reajason/xhs 库的API接口
  - [x] SubTask 2.2: 在 backend/app/services/ 新增 platform_scraper/xhs_scraper.py，封装小红书数据抓取逻辑
  - [x] SubTask 2.3: 复用 scraper.py API，扩展支持小红书平台抓取
  - [x] SubTask 2.4: 新增定时任务：每日自动抓取小红书热门笔记数据
  - [x] SubTask 2.5: 实现小红书Cookie/登录态管理

- [x] Task 3: 集成自动发布服务
  - [x] SubTask 3.1: 调研 dreammis/social-auto-upload 的 uploader 模块架构，确定集成方式
  - [x] SubTask 3.2: 在 backend/app/services/ 新增 auto_publisher.py，封装自动发布逻辑
  - [x] SubTask 3.3: 新增 POST /api/v1/tasks/{id}/auto-publish API
  - [x] SubTask 3.4: 修改前端 TaskDetail.vue，"我已发布"按钮改为"一键发布"（优先自动发布，失败降级手动）
  - [x] SubTask 3.5: 实现 Cookie 管理：存储/刷新/过期检测
  - [x] SubTask 3.6: 实现发布结果回调：成功自动更新任务状态，失败提示手动发布

- [x] Task 4: 集成爆款结构自动提取
  - [x] SubTask 4.1: 调研 viral-video-analyzer 的API接口和输出格式
  - [x] SubTask 4.2: 在 backend/app/services/ 新增 structure_extractor.py，封装爆款结构提取逻辑
  - [x] SubTask 4.3: 新增 POST /api/v1/admin/extract-structure API（管理员提交爆款视频URL）
  - [x] SubTask 4.4: 提取结果自动写入 content_structures 表（钩子类型/情绪结构/转化信号）
  - [x] SubTask 4.5: 管理后台新增"爆款提取"功能入口

## 第 2 阶段：P1 进化引擎增强

- [x] Task 5: 集成评论情感分析
  - [x] SubTask 5.1: pip install snownlp，编写情感分析工具函数
  - [x] SubTask 5.2: 在数据抓取流程中增加评论情感分析步骤
  - [x] SubTask 5.3: 新增 comment_sentiment 字段到 market_hots 表，存储情感分析结果
  - [x] SubTask 5.4: 修改诊断服务，将评论情感数据纳入诊断依据（正面多→结构有效，负面多→需优化）
  - [x] SubTask 5.5: 管理后台展示评论情感分析结果

- [x] Task 6: 实现用户行为事件追踪
  - [x] SubTask 6.1: 新增 user_events 数据模型（event_type/page/duration/metadata/timestamp）
  - [x] SubTask 6.2: 新增 POST /api/v1/events 批量上报API
  - [x] SubTask 6.3: 前端埋点：页面停留时长、意图选择、任务查看、内容复制、发布点击
  - [x] SubTask 6.4: 修改诊断服务，将用户行为数据纳入诊断（如：用户复制了口播但没点发布→内容可能不够吸引）
  - [x] SubTask 6.5: 管理后台新增用户行为分析面板

## 第 3 阶段：P2 安全与体验完善

- [x] Task 7: 实现管理后台RBAC权限控制
  - [x] SubTask 7.1: users 表新增 role 字段（admin/user），默认 user
  - [x] SubTask 7.2: 修改 JWT token 生成，包含 role 信息
  - [x] SubTask 7.3: 新增 require_admin 依赖注入，保护 /api/v1/admin/* 路由
  - [x] SubTask 7.4: 新增用户角色管理 API（仅管理员可操作）
  - [x] SubTask 7.5: 前端根据角色显示/隐藏管理入口

- [x] Task 8: 集成真实短信验证码
  - [x] SubTask 8.1: pip install senweaver-sms，配置短信服务商（阿里云/腾讯云）
  - [x] SubTask 8.2: 新增 backend/app/services/sms_service.py，封装验证码发送和校验逻辑
  - [x] SubTask 8.3: 修改登录 API，替换硬编码 123456 为真实验证码
  - [x] SubTask 8.4: 新增验证码缓存（Redis或内存缓存，5分钟过期）
  - [x] SubTask 8.5: 新增 .env 配置项：SMS_GATEWAY/ACCESS_KEY/SECRET_KEY/SIGN_NAME

# Task Dependencies

- Task 2 depends on Task 1 (共享 scraper API 和 market_service 修改)
- Task 4 depends on Task 1 or Task 2 (需要先有数据抓取能力才能提取结构)
- Task 5 depends on Task 1 or Task 2 (需要先有评论数据才能做情感分析)
- Task 6 is independent
- Task 7 is independent
- Task 8 is independent
