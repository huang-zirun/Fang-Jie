# 开源替代方案调研与集成 Spec

## Why

需求对照分析文档显示 142 项需求中 44 项(31%)完全未实现，核心缺口集中在：实时数据引擎(0/10)、自动闭环(数据抓取+自动发布)、护城河验证机制。通过复用 GitHub 上成熟的开源项目，可以大幅降低从零实现的成本和风险。

## What Changes

- 引入开源数据抓取方案替代手动数据回填，打通自动闭环
- 引入自动发布工具替代手动复制发布
- 引入轻量级情感分析库实现评论内容分析
- 引入爆款视频分析工具实现内容结构自动提取
- 引入 RBAC 权限控制方案替代无权限管理
- 引入短信 SDK 替代硬编码验证码
- 引入轻量级事件追踪方案替代无用户行为数据

## Impact

- Affected specs: 实时数据引擎、学习进化引擎、前台交互层、后台管理
- Affected code: backend/app/services/、backend/app/api/、frontend/src/views/

---

## 调研结果汇总

### 缺口 1：抖音/小红书数据抓取（P0 核心缺失）

> 对应需求：2.2 实时数据引擎、1.4 系统自动接管、6.1-6.7 数据源集成

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **Evil0ctal/Douyin_TikTok_Download_API** | 18k | Python/FastAPI | MIT | ⭐⭐⭐⭐ | 高性能异步抖音/TikTok数据爬取，FastAPI原生，支持API调用、批量解析、无水印下载。与本项目技术栈完全一致(FastAPI+异步) |
| **JoeanAmier/TikTokDownloader** | 14.5k | Python | MIT | ⭐⭐⭐⭐ | 抖音发布/喜欢/收藏/评论/搜索/热榜数据采集。功能最全面，支持评论抓取、账号数据、搜索热榜 |
| **vsmutok/douyin-scraper** | 较新 | Python | MIT | ⭐⭐⭐ | 生产级抖音搜索爬虫，Playwright+Docker化，支持验证码自动解决，输出结构化JSON |
| **reajason/xhs** | 活跃 | Python | MIT | ⭐⭐⭐⭐ | 小红书Web端请求封装(pip install xhs)，签名自动处理，支持笔记/评论/用户信息获取，二维码登录 |
| **XiaohongshuSpider** | 有名 | Python | Apache-2.0 | ⭐⭐ | Appium+MitmProxy方案，需安卓模拟器，部署复杂，不推荐 |

**推荐方案**：
- **抖音**：集成 `JoeanAmier/TikTokDownloader` 的数据采集模块（评论/热榜/搜索），或 `Evil0ctal/Douyin_TikTok_Download_API` 作为微服务
- **小红书**：集成 `reajason/xhs` 库（pip install xhs），最轻量、API最友好
- **风险提示**：所有爬虫方案都存在平台反爬导致的稳定性问题，需设计降级策略（爬取失败时回退到手动录入）

### 缺口 2：自动发布到平台（P0 闭环关键）

> 对应需求：1.3.8 唯一按钮、1.5.3 用户执行、3.5 用户执行

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **dreammis/social-auto-upload** | 11.2k | Python/Playwright | Apache-2.0 | ⭐⭐⭐⭐⭐ | 自动化上传视频到抖音/小红书/视频号/B站/快手/TikTok，Playwright模拟真实操作，支持定时发布、Cookie管理、多账号 |

**推荐方案**：
- 集成 `social-auto-upload` 作为自动发布引擎
- 将其 uploader 模块抽取为独立服务，通过 API 调用
- 前端"我已发布"按钮改为"一键发布"，调用自动发布服务
- **风险提示**：基于Playwright模拟操作，平台UI变更可能导致失效；需Cookie维护

### 缺口 3：评论内容分析/情感分析（P1 进化引擎需要）

> 对应需求：2.2.7 提取能力：看用户反馈、2.4.4 输入：用户行为、6.8 评论内容分析

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **SnowNLP** | - | Python | MIT | ⭐⭐⭐⭐⭐ | 轻量级中文情感分析(pip install snownlp)，0~1情感分值，零配置，适合短文本评论分析 |
| **PaddleNLP** | 极高 | Python | Apache-2.0 | ⭐⭐⭐ | 百度飞桨NLP套件，TextCNN/BERT情感分析，精度高但依赖重 |
| **Hey-Sweety/Short-Texts-Sentiment-Analyse** | 中等 | Python | - | ⭐⭐⭐ | 中文短文本情感分析对比实验，含情感词典法/机器学习/深度学习/预训练微调四种方法 |

**推荐方案**：
- **首选 SnowNLP**：最轻量，`pip install snownlp` 即可，适合 MVP 阶段快速集成
- 对评论文本计算情感分值，自动识别"正面/中性/负面"倾向
- 后续可升级到 PaddleNLP 或直接用 DeepSeek AI 做深度分析

### 缺口 4：爆款内容结构自动提取（P0 实时数据引擎核心）

> 对应需求：2.2.5 提取能力：看结构、2.2.6 提取能力：看转化信号、6.9 爆款结构自动提取

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **pelpeljakob-creator/viral-video-analyzer** | 新 | Python/FastAPI | MIT | ⭐⭐⭐⭐⭐ | AI驱动爆款短视频拉片分析工具，FastAPI后端+SSE流式响应，自动拆解视频结构（钩子/冲突/高潮/转化），与本项目技术栈完全一致 |
| **datawhalechina/video-devour** | 活跃 | Python | MIT | ⭐⭐⭐⭐ | 智能视频到报告生成器，ASR语音识别+VLM视觉分析，生成结构化报告含大纲/关键帧/摘要 |
| **el-frontend/video-wizard** | 中等 | Python | - | ⭐⭐⭐ | AI视频内容分析+viral clip识别+字幕生成，GPT-4o打分(0-100) |
| **AI-Nate/Cut-AI** | 新 | Python | MIT | ⭐⭐⭐ | 自动从长视频提取viral highlight clips，Gemini+Claude |

**推荐方案**：
- **首选 viral-video-analyzer**：FastAPI 原生，爆款结构拆解逻辑与本项目需求高度吻合
- 输入爆款视频URL → 自动提取钩子类型/情绪结构/转化信号 → 写入 content_structures 表
- **备选 video-devour**：更全面的视频分析能力（ASR+关键帧），但更重

### 缺口 5：管理后台权限控制（P2）

> 对应需求：7.5 管理后台权限控制

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **fastapiadmin/FastapiAdmin** | 活跃 | Python/Vue3 | MIT | ⭐⭐⭐ | FastAPI+Vue3+RBAC权限控制，JWT+OAuth2，菜单/按钮/数据级权限。但需MySQL/MongoDB+Redis，与本项目SQLite不兼容 |
| **Pranjalm-23/fastapi-rbac-jwt-api** | 小 | Python | Apache-2.0 | ⭐⭐⭐ | 纯FastAPI RBAC+JWT实现，代码简洁可参考，但用MongoDB |
| 自行实现 | - | Python | - | ⭐⭐⭐⭐ | 基于FastAPI Depends+JWT的最简RBAC，SQLite兼容，参考上述项目代码模式 |

**推荐方案**：
- **自行实现轻量级RBAC**：FastapiAdmin 太重（需MySQL+Redis），与本项目SQLite架构不兼容
- 参考 fastapi-rbac-jwt-api 的代码模式，实现 admin/user 两级角色
- 在现有 JWT 中间件基础上增加 role 字段，admin API 加 role 校验装饰器

### 缺口 6：短信验证码（P2）

> 对应需求：7.8 手机号真实验证码

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **senweaver/senweaver-sms** | 新 | Python | MIT | ⭐⭐⭐⭐⭐ | Python短信聚合SDK，Builder API，支持阿里云/腾讯云/华为云等10+服务商，统一接口，轮询策略 |
| 阿里云号码认证SDK | 官方 | Python | 官方 | ⭐⭐⭐⭐ | 个人开发者免资质接入，预置签名和模板，pip install alibabacloud_dypnsapi20170525 |
| 腾讯云短信SDK | 官方 | Python | 官方 | ⭐⭐⭐⭐ | pip install qcloudsms_py，需企业认证 |

**推荐方案**：
- **首选 senweaver-sms**：统一接口，多服务商轮询，切换只需改配置
- **个人开发者场景**：阿里云号码认证服务（免资质）
- 替换当前硬编码 123456 验证码

### 缺口 7：用户行为追踪（P1 进化引擎需要）

> 对应需求：2.4.4 输入：用户行为、7.4 图文笔记生成入口

| 项目 | Stars | 语言 | 协议 | 可复用度 | 说明 |
|------|-------|------|------|---------|------|
| **PostHog** | 24.2k | Python/Django | MIT | ⭐⭐ | 功能最全（事件追踪+漏斗+留存+会话录制），但需PostgreSQL+Redis，太重 |
| **Umami** | 活跃 | Node.js | MIT | ⭐⭐ | 轻量级分析，需MySQL/PostgreSQL，Node.js部署 |
| 自行实现 | - | Python | - | ⭐⭐⭐⭐⭐ | 基于FastAPI+SQLite的最简事件追踪，记录用户操作行为到 user_events 表 |

**推荐方案**：
- **自行实现轻量级事件追踪**：PostHog/Umami 都需要额外数据库，与本项目SQLite架构不兼容
- 新增 user_events 表，记录事件类型/页面/时长/元数据
- 前端埋点：页面停留时长、按钮点击、内容复制等关键行为
- 后端 API：POST /api/v1/events 批量上报

---

## 优先级排序与实施建议

### 第一优先级（P0 - 核心闭环打通）

| 序号 | 缺口 | 推荐方案 | 预估工作量 | 依赖 |
|------|------|---------|-----------|------|
| 1 | 抖音数据抓取 | JoeanAmier/TikTokDownloader 数据模块 | 中 | 无 |
| 2 | 小红书数据抓取 | reajason/xhs 库 | 小 | 无 |
| 3 | 自动发布 | dreammis/social-auto-upload uploader模块 | 中 | 无 |
| 4 | 爆款结构提取 | viral-video-analyzer | 中 | 1或2 |

### 第二优先级（P1 - 进化引擎增强）

| 序号 | 缺口 | 推荐方案 | 预估工作量 | 依赖 |
|------|------|---------|-----------|------|
| 5 | 评论情感分析 | SnowNLP | 小 | 1或2 |
| 6 | 用户行为追踪 | 自行实现(轻量) | 中 | 无 |

### 第三优先级（P2 - 安全与体验完善）

| 序号 | 缺口 | 推荐方案 | 预估工作量 | 依赖 |
|------|------|---------|-----------|------|
| 7 | 管理后台权限 | 自行实现RBAC | 小 | 无 |
| 8 | 短信验证码 | senweaver-sms | 小 | 无 |

---

## ADDED Requirements

### Requirement: 平台数据自动抓取服务

系统 SHALL 提供抖音和小红书平台的数据自动抓取能力，替代当前的手动数据回填。

#### Scenario: 抖音爆款数据抓取
- **WHEN** 定时任务触发或用户请求抓取抖音数据
- **THEN** 系统调用 TikTokDownloader 数据模块，抓取指定关键词下的爆款视频元数据（播放量/评论数/分享数/发布时间）
- **AND** 将抓取结果写入 market_hots 表，自动更新 market_score

#### Scenario: 小红书热帖数据抓取
- **WHEN** 定时任务触发或用户请求抓取小红书数据
- **THEN** 系统调用 xhs 库，抓取指定关键词下的热门笔记数据（点赞/收藏/评论数）
- **AND** 将抓取结果写入 market_hots 表

#### Scenario: 抓取失败降级
- **WHEN** 平台反爬导致抓取失败
- **THEN** 系统记录失败日志，回退到手动录入模式，不阻塞用户正常使用

### Requirement: 自动发布服务

系统 SHALL 提供一键发布内容到抖音/小红书的能力，替代当前的手动复制发布。

#### Scenario: 一键发布到抖音
- **WHEN** 用户点击"一键发布"按钮并选择抖音平台
- **THEN** 系统调用 social-auto-upload 的抖音 uploader，自动上传视频/图文内容
- **AND** 发布成功后自动更新任务状态为 PUBLISHED

#### Scenario: 发布失败处理
- **WHEN** 自动发布因Cookie过期或平台限制失败
- **THEN** 系统提示用户手动发布，并提供复制内容的一键操作

### Requirement: 评论情感分析

系统 SHALL 对抓取到的评论内容进行自动情感分析，为学习进化引擎提供用户反馈信号。

#### Scenario: 评论情感分析
- **WHEN** 系统抓取到视频/笔记的评论数据
- **THEN** 使用 SnowNLP 对每条评论计算情感分值（0~1）
- **AND** 统计正面/中性/负面比例，写入诊断数据

### Requirement: 爆款内容结构自动提取

系统 SHALL 从爆款视频中自动提取内容结构模式，反哺爆款结构引擎。

#### Scenario: 爆款结构提取
- **WHEN** 运营人员在管理后台提交爆款视频URL
- **THEN** 系统调用 viral-video-analyzer 分析视频结构（钩子类型/情绪曲线/转化信号）
- **AND** 将提取的结构模式写入 content_structures 表作为新模板

### Requirement: 管理后台RBAC权限控制

系统 SHALL 对管理后台实施基于角色的访问控制。

#### Scenario: 非管理员访问管理后台
- **WHEN** 普通用户尝试访问 /admin 路径
- **THEN** 系统返回 403 Forbidden

#### Scenario: 管理员操作
- **WHEN** 管理员登录后访问管理后台
- **THEN** 系统允许全部 CRUD 操作

### Requirement: 真实短信验证码

系统 SHALL 使用真实短信服务发送验证码，替代硬编码的 123456。

#### Scenario: 发送验证码
- **WHEN** 用户输入手机号请求登录
- **THEN** 系统通过 senweaver-sms 调用配置的短信服务商发送6位数字验证码
- **AND** 验证码5分钟内有效

### Requirement: 用户行为事件追踪

系统 SHALL 记录用户在前端的关键操作行为，为学习进化引擎提供行为数据。

#### Scenario: 行为事件上报
- **WHEN** 用户在前端执行操作（选择意图/查看任务/复制内容/点击发布）
- **THEN** 前端将事件类型/时间戳/页面/元数据上报到 POST /api/v1/events
- **AND** 后端将事件写入 user_events 表
