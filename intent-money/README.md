# Intent Money OS — 意图选择式赚钱系统

> 一个面向袜子分销创作者的 AI 驱动内容生成与优化平台。用户选择赚钱意图，系统自动生成适配抖音/小红书等平台的短视频脚本、图文笔记，并通过数据回填实现闭环诊断与内容迭代优化。

***

## 项目简介

Intent Money OS 帮助没有内容策划经验的普通用户，通过"选择意图 → 获取内容任务 → 发布 → 回填数据 → 获得诊断 → 获取优化任务"的闭环流程，持续产出高转化内容。

核心解决三个问题：

- **不知道拍什么** — AI 根据意图+平台结构自动生成完整内容方案
- **不知道哪里不好** — 基于播放量/评论/私信数据的规则引擎自动诊断
- **不知道怎么改** — 诊断结果驱动下一条内容针对性优化

***

## 技术栈

| 层级        | 技术                                         |
| --------- | ------------------------------------------ |
| **前端**    | Vue 3 + TypeScript + Vite + Vant 4（移动端 UI） |
| **后端**    | FastAPI + SQLAlchemy 2.0（异步 ORM）           |
| **数据库**   | SQLite（aiosqlite 异步驱动）                     |
| **AI 模型** | DeepSeek V3（via OpenRouter API）            |
| **部署**    | Docker Compose（FastAPI + Frontend + Nginx） |
| **迁移**    | Alembic                                    |

***

## 项目结构

```
intent-money/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API 路由（auth, intents, tasks, content_structures, admin）
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   ├── schemas/            # Pydantic 校验模型
│   │   ├── services/           # 业务逻辑（AI 生成、任务生成、诊断、清理）
│   │   ├── utils/              # 工具函数（安全、加密）
│   │   ├── main.py             # FastAPI 应用入口
│   │   ├── config.py           # 环境配置
│   │   ├── database.py         # 数据库连接与会话管理
│   │   └── seed.py             # 初始数据种子
│   ├── tests/                  # 测试用例
│   ├── alembic/                # 数据库迁移
│   ├── pyproject.toml          # Python 依赖（uv 管理）
│   └── alembic.ini             # Alembic 配置
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面（IntentSelect, TaskDetail, DataReport）
│   │   ├── api/                # HTTP 请求封装
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # Vue Router 配置
│   │   ├── styles/             # 全局样式
│   │   └── main.ts             # 应用入口
│   ├── package.json            # Node 依赖
│   └── vite.config.ts          # Vite 配置
│
├── docker/                     # Docker 部署配置
│   ├── docker-compose.yml      # 服务编排
│   └── nginx.conf              # Nginx 反向代理
│
└── .github/workflows/          # CI 配置
```

***

## 核心功能

### 1. 意图选择（IntentSelect）

用户从预设的赚钱意图中选择一个（如"好物推荐"、"知识分享"等），系统据此匹配内容结构模板。

### 2. AI 内容生成

根据意图 + 平台 + 内容结构模板，调用 DeepSeek 生成：

- **3秒钩子文案** — 前3秒吸引注意力的开场白
- **分镜脚本** — 3-5 个镜头的拍摄/图片指导
- **口播文案** — 100-200 字的完整话术
- **发布标题** — 含话题标签的标题
- **评论区话术** — 引导私信或互动的置顶评论
- **为什么能赚钱** — 一句话解释转化逻辑

内置禁用词过滤（绝对化用语、医疗承诺、虚假收益等）和关键词校验（必须包含"袜子"）。

### 3. 任务生命周期管理

```
PENDING → PUBLISHED → REPORTED → DIAGNOSED → (next task) → PENDING
```

- **PENDING**: 刚生成，用户可发布或换一条（每日限1次）
- **PUBLISHED**: 用户确认已发布，等待数据回填
- **REPORTED**: 已提交播放量/评论数/私信数
- **DIAGNOSED**: AI 诊断完成，可获取下一条优化任务

### 4. 数据诊断与优化（DataReport）

用户回填内容数据后，规则引擎根据预设条件自动诊断：

| 问题类型              | 触发条件    | 优化方向    |
| ----------------- | ------- | ------- |
| hook\_weak        | 播放量极低   | 更换钩子策略  |
| title\_weak       | 播放量偏低   | 优化标题/选题 |
| interaction\_weak | 播放高但评论少 | 增强互动引导  |
| conversion\_weak  | 评论多但私信0 | 优化转化话术  |
| normal            | 数据正常    | 保持当前策略  |

诊断结果驱动下一条任务生成时注入优化约束，实现内容迭代。

### 5. 匿名用户系统

- 手机验证码注册/登录
- JWT Token 认证（7天有效期）
- 无需密码，降低使用门槛

***

## 数据模型

| 实体                    | 说明                               |
| --------------------- | -------------------------------- |
| **User**              | 用户（手机号、匿名标识）                     |
| **Intent**            | 赚钱意图（名称、描述、排序、激活状态）              |
| **Platform**          | 发布平台（抖音、小红书等）                    |
| **ContentStructure**  | 内容结构模板（钩子类型、情绪结构、转化结构、Prompt 模板） |
| **ContentTask**       | 内容任务（钩子、脚本、标题、状态、优化标记）           |
| **PerformanceReport** | 表现报告（播放量、评论数、私信数）                |
| **DiagnosisResult**   | 诊断结果（问题类型、优化方向、优化详情）             |
| **OptimizationRule**  | 优化规则（条件表达式、问题类型、优化 Prompt）       |
| **Session**           | 用户会话管理                           |

***

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18
- uv（Python 包管理器）

### 后端启动

```bash
cd backend

# 安装依赖
uv sync

# 运行迁移
uv run alembic upgrade head

# 启动服务
uv run uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev
```

### Docker 部署

```bash
cd docker

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 AI_API_KEY

# 启动全部服务
docker-compose up -d
```

***

## 环境变量

| 变量             | 默认值                                     | 说明                |
| -------------- | --------------------------------------- | ----------------- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./intent_money.db` | 数据库连接             |
| `SECRET_KEY`   | `change-me-in-production`               | JWT 密钥            |
| `AI_API_KEY`   | —                                       | OpenRouter API 密钥 |
| `AI_BASE_URL`  | `https://openrouter.ai/api/v1`          | AI API 地址         |
| `AI_MODEL`     | `deepseek/deepseek-chat-v3-0324:free`   | 默认模型              |
| `ENV`          | `development`                           | 运行环境              |

***

## API 概览

| 方法   | 路径                             | 说明        |
| ---- | ------------------------------ | --------- |
| POST | `/api/v1/auth/register`        | 用户注册      |
| POST | `/api/v1/auth/login`           | 用户登录      |
| GET  | `/api/v1/intents`              | 获取意图列表    |
| POST | `/api/v1/tasks`                | 创建内容任务    |
| GET  | `/api/v1/tasks/current`        | 获取当前任务    |
| POST | `/api/v1/tasks/{id}/publish`   | 确认发布      |
| POST | `/api/v1/tasks/{id}/swap`      | 换一条任务     |
| POST | `/api/v1/tasks/{id}/report`    | 提交数据报告    |
| POST | `/api/v1/tasks/{id}/next`      | 获取下一条优化任务 |
| GET  | `/api/v1/tasks/{id}/diagnosis` | 获取诊断结果    |

***

## 测试

```bash
cd backend

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run mypy .
```

***

