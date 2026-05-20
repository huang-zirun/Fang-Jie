# Tasks

## 第 1 阶段：闭环骨架

* [x] Task 1: 初始化项目结构

  * [x] SubTask 1.1: 创建 monorepo 目录结构（frontend / backend / docker）

  * [x] SubTask 1.2: 初始化 FastAPI 后端项目（pyproject.toml + uv + 基础目录结构）

  * [x] SubTask 1.3: 初始化 Vue 3 前端项目（Vite + TypeScript + Vant + Pinia + Vue Router）

  * [x] SubTask 1.4: 创建 Docker Compose 配置（FastAPI + PostgreSQL + Nginx）

  * [x] SubTask 1.5: 配置基础 CI（lint + typecheck）

* [x] Task 2: 数据库 schema 与基础 API

  * [x] SubTask 2.1: 创建数据库迁移脚本（users, user_sessions, intents, platforms, content_structures, content_tasks, performance_reports, diagnosis_results, optimization_rules）

  * [x] SubTask 2.2: 创建 SQLAlchemy models

  * [x] SubTask 2.3: 实现意图列表 API（GET /api/v1/intents）

  * [x] SubTask 2.4: 种子数据脚本（intents + platforms 初始数据）

* [x] Task 3: 用户与会话模块

  * [x] SubTask 3.1: 实现匿名注册 API（POST /api/v1/auth/anonymous）

  * [x] SubTask 3.2: 实现 JWT 生成与验证中间件

  * [x] SubTask 3.3: 实现手机号登录 API（POST /api/v1/auth/login）含验证码逻辑

  * [x] SubTask 3.4: 前端 JWT 存储与请求拦截器

* [x] Task 4: 前端首屏与任务界面骨架

  * [x] SubTask 4.1: 实现意图选择首屏（4 个按钮，仅"引流拿客户"可点击）

  * [x] SubTask 4.2: 实现任务界面骨架（固定模板内容，展示钩子/分镜/口播/标题/话术）

  * [x] SubTask 4.3: 实现"我已发布"按钮与确认流程

  * [x] SubTask 4.4: 实现任务生成 API（POST /api/v1/tasks，先用固定模板不接 AI）

  * [x] SubTask 4.5: 实现发布确认 API（POST /api/v1/tasks/{id}/publish）

## 第 2 阶段：任务生成与结构库

* [x] Task 5: 内容结构库模块

  * [x] SubTask 5.1: 实现 content_structures CRUD API

  * [x] SubTask 5.2: 实现按意图+平台匹配结构的查询逻辑

  * [x] SubTask 5.3: 创建初始结构库种子数据（至少 20 个结构模板）

  * [x] SubTask 5.4: 运营后台：结构模板管理页面

* [x] Task 6: AI 内容生成集成

  * [x] SubTask 6.1: 实现 Claude API 调用封装（超时、重试、错误处理）

  * [x] SubTask 6.2: 实现 Prompt 构造逻辑（意图+平台+结构模板+优化约束）

  * [x] SubTask 6.3: 实现 AI 输出解析与校验（JSON 格式、字段完整性、违规词检测）

  * [x] SubTask 6.4: 实现 fallback 兜底逻辑（AI 失败时使用结构库预置文案）

  * [x] SubTask 6.5: 实现 AI 调用日志记录（token 用量、耗时、是否成功）

  * [x] SubTask 6.6: 改造任务生成 API，接入 AI 替代固定模板

* [x] Task 7: 换一条与图文模式

  * [x] SubTask 7.1: 实现"换一条"API（POST /api/v1/tasks/{id}/swap，每天限 1 次）

  * [x] SubTask 7.2: 实现图文模式切换（task_type: video/image）

  * [x] SubTask 7.3: 前端：换一条按钮与次数提示

  * [x] SubTask 7.4: 前端：视频/图文模式切换 UI

* [x] Task 8: 前端任务界面完善

  * [x] SubTask 8.1: 适配动态 AI 生成内容渲染

  * [x] SubTask 8.2: 实现"为什么这条内容能赚钱"展示

  * [x] SubTask 8.3: 实现分镜脚本可视化展示

  * [x] SubTask 8.4: 加载状态优化（骨架屏）

## 第 3 阶段：数据回传与规则诊断

* [x] Task 9: 数据回传模块

  * [x] SubTask 9.1: 实现数据回传 API（POST /api/v1/tasks/{id}/report）

  * [x] SubTask 9.2: 实现输入校验（范围、类型、重复提交）

  * [x] SubTask 9.3: 前端：数据回填表单（播放量/评论数/私信数）

  * [x] SubTask 9.4: 前端：已发布任务列表与回填入口

* [x] Task 10: 规则诊断模块

  * [x] SubTask 10.1: 实现 optimization_rules CRUD API

  * [x] SubTask 10.2: 创建初始诊断规则种子数据

  * [x] SubTask 10.3: 实现规则诊断引擎（按优先级匹配规则，输出问题类型+优化方向）

  * [x] SubTask 10.4: 实现诊断结果存储与查询 API（GET /api/v1/tasks/{id}/diagnosis）

  * [x] SubTask 10.5: 运营后台：诊断规则管理页面

* [x] Task 11: 诊断结果展示

  * [x] SubTask 11.1: 前端：诊断结果页面（问题类型+优化方向+具体建议）

  * [x] SubTask 11.2: 前端："获取下一条任务"入口

  * [x] SubTask 11.3: 实现 24h/48h 未回填提醒逻辑

## 第 4 阶段：优化任务与上线验证

* [ ] Task 12: 下一条优化任务

  * [ ] SubTask 12.1: 实现优化约束注入 Prompt 逻辑

  * [ ] SubTask 12.2: 实现下一条任务 API（POST /api/v1/tasks/{id}/next）

  * [ ] SubTask 12.3: 实现优化说明生成（改了什么、为什么改）

  * [ ] SubTask 12.4: 前端：优化任务展示（标注"已优化"+ 优化说明）

* [ ] Task 13: 异常流程处理

  * [ ] SubTask 13.1: 用户有未完成任务时的提示与选择逻辑

  * [ ] SubTask 13.2: 结构库为空时的错误处理

  * [ ] SubTask 13.3: 任务过期逻辑（48h 未回填自动 EXPIRED）

  * [ ] SubTask 13.4: 前端：各异常场景的提示 UI

* [ ] Task 14: 运营后台完善

  * [ ] SubTask 14.1: 用户数据统计面板（任务数、发布率、回填率）

  * [ ] SubTask 14.2: AI 调用日志查看

  * [ ] SubTask 14.3: 禁用词列表配置

  * [ ] SubTask 14.4: AI Prompt 模板配置

* [ ] Task 15: 端到端测试与上线

  * [ ] SubTask 15.1: 后端单元测试（核心模块覆盖率 ≥ 80%）

  * [ ] SubTask 15.2: API 集成测试

  * [ ] SubTask 15.3: 前端 E2E 测试（核心闭环）

  * [ ] SubTask 15.4: 部署脚本与生产环境配置

  * [ ] SubTask 15.5: 种子用户验证与 KPI 统计埋点

所有任务完成之后需要记载到记忆系统，如果jouney没有搭建，需要先搭建。

# Task Dependencies

* Task 2 depends on Task 1

* Task 3 depends on Task 1

* Task 4 depends on Task 2, Task 3

* Task 5 depends on Task 2

* Task 6 depends on Task 5

* Task 7 depends on Task 6

* Task 8 depends on Task 6

* Task 9 depends on Task 4

* Task 10 depends on Task 9

* Task 11 depends on Task 10

* Task 12 depends on Task 10, Task 6

* Task 13 depends on Task 12

* Task 14 depends on Task 6, Task 10

* Task 15 depends on Task 12, Task 13, Task 14

