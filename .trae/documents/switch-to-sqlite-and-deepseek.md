# 计划：PostgreSQL → SQLite + AI 模型切换至 DeepSeek V4 Flash

## 概述

三项变更：

1. 将 PostgreSQL 数据库替换为 SQLite（使用 aiosqlite 异步驱动）
2. AI 模型从 Claude (Anthropic SDK) 切换为 DeepSeek V4 Flash（通过 OpenRouter API）
3. 更新 `AGENTS.md` 记忆系统记录变更

***

## 一、数据库：PostgreSQL → SQLite

### 1.1 依赖变更 (`backend/pyproject.toml`)

* **移除**：`asyncpg`

* **新增**：`aiosqlite`

* **保留**：`sqlalchemy[asyncio]`、`alembic` 等不变

### 1.2 配置变更 (`backend/app/config.py`)

* `DATABASE_URL` 默认值改为 `sqlite+aiosqlite:///./intent_money.db`

* 新增 `AI_API_KEY` 配置项（替代 `CLAUDE_API_KEY`）

* 新增 `AI_BASE_URL` 配置项（默认 `https://openrouter.ai/api/v1`）

* 新增 `AI_MODEL` 配置项（默认 `deepseek/deepseek-chat-v3-0324:free` 或 DeepSeek 官方模型名）

### 1.3 数据库引擎 (`backend/app/database.py`)

* SQLite 异步引擎需要额外参数：

  * `connect_args={"check_same_thread": False}`（解决 SQLite 线程检查问题）

  * 在引擎创建时添加 `@event.listens_for(engine.sync_engine, "connect")` 事件，启用 `PRAGMA foreign_keys=ON`（SQLite 默认不启用外键约束）

* 移除 PostgreSQL 特有的引擎参数

### 1.4 模型变更（9 个模型文件）

所有模型中使用了 PostgreSQL 特有类型，需替换：

| PostgreSQL 类型                                      | SQLite 替代                                         |
| -------------------------------------------------- | ------------------------------------------------- |
| `from sqlalchemy.dialects.postgresql import UUID`  | `from sqlalchemy import Uuid`（SQLAlchemy 2.0+ 内置） |
| `UUID(as_uuid=True)`                               | `Uuid(as_uuid=True)`                              |
| `from sqlalchemy.dialects.postgresql import JSONB` | `from sqlalchemy import JSON`                     |
| `JSONB`                                            | `JSON`                                            |

受影响文件：

* `backend/app/models/user.py` — 无 PG 特有类型（UUID 主键用内置类型即可）

* `backend/app/models/session.py` — `UUID` → `Uuid`

* `backend/app/models/intent.py` — `UUID` → `Uuid`

* `backend/app/models/platform.py` — `UUID` → `Uuid`

* `backend/app/models/content_structure.py` — `UUID` → `Uuid`, `JSONB` → `JSON`

* `backend/app/models/content_task.py` — `UUID` → `Uuid`, `JSONB` → `JSON`

* `backend/app/models/performance_report.py` — `UUID` → `Uuid`

* `backend/app/models/diagnosis_result.py` — `UUID` → `Uuid`

* `backend/app/models/optimization_rule.py` — `UUID` → `Uuid`, `JSONB` → `JSON`

### 1.5 Alembic 迁移 (`backend/alembic/env.py`)

* 当前使用 `async_engine_from_config`，SQLite 兼容此方式

* 无需大幅修改，但需确保 `alembic.ini` 中的 `sqlalchemy.url` 更新

### 1.6 Alembic 配置 (`backend/alembic.ini`)

* `sqlalchemy.url` 改为 `sqlite+aiosqlite:///./intent_money.db`

* 注意：SQLite 不支持 `ALTER TABLE` 的某些操作（如 DROP COLUMN），Alembic 需配置 `render_as_batch=True`

在 `alembic/env.py` 的 `do_run_migrations` 中添加：

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,  # SQLite 兼容
)
```

### 1.7 Docker Compose (`docker/docker-compose.yml`)

* **移除** `db` 服务（PostgreSQL 容器）

* **移除** `postgres_data` volume

* **移除** `backend` 的 `depends_on: db`

* **移除** `backend` 环境变量中的 `DATABASE_URL`（使用默认 SQLite 路径即可）

* 如果需要持久化，将 SQLite 数据库文件挂载为 volume

### 1.8 种子数据 (`backend/app/seed.py`)

* 无需修改，SQLAlchemy ORM 抽象层已处理方言差异

### 1.9 测试配置 (`backend/tests/conftest.py`)

* 测试使用内存 SQLite：`sqlite+aiosqlite://` 或 `sqlite+aiosqlite:///./test.db`

***

## 二、AI 模型：Claude → DeepSeek V4 Flash (OpenRouter)

### 2.1 依赖变更 (`backend/pyproject.toml`)

* **移除**：`anthropic>=0.103.1`

* **新增**：`openai>=1.0.0`（OpenRouter 兼容 OpenAI SDK）

### 2.2 AI 服务重写 (`backend/app/services/ai_service.py`)

核心变更：

* 移除 `from anthropic import Anthropic, APIError, APITimeoutError`

* 改用 `from openai import AsyncOpenAI, APIError, APITimeoutError`

* 客户端初始化改为：

  ```python
  client = AsyncOpenAI(
      api_key=settings.AI_API_KEY,
      base_url=settings.AI_BASE_URL,
  )
  ```

* API 调用改为原生异步（不再需要 `asyncio.to_thread`）：

  ```python
  response = await client.chat.completions.create(
      model=settings.AI_MODEL,
      max_tokens=1024,
      messages=[{"role": "user", "content": prompt}],
  )
  ```

* 响应解析改为：

  ```python
  text = response.choices[0].message.content
  ```

* token 用量改为：

  ```python
  response.usage.prompt_tokens, response.usage.completion_tokens
  ```

* 异常处理：`openai` 库的 `APIError`、`APITimeoutError` 与 `anthropic` 同名，直接替换 import 即可

### 2.3 配置变更 (`backend/app/config.py`)

* 移除 `CLAUDE_API_KEY`

* 新增：

  * `AI_API_KEY: str | None = None`

  * `AI_BASE_URL: str = "https://openrouter.ai/api/v1"`

  * `AI_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"`

### 2.4 测试 (`backend/tests/test_ai_service.py`)

* 现有测试仅测试 `_validate_output` 和 `BANNED_PHRASES`，不涉及 API 调用，无需修改

***

## 三、更新 AGENTS.md 记忆系统

### 3.1 更新 `AGENTS.md`

在文件中追加或更新项目技术栈说明，记录：

* 数据库已从 PostgreSQL 更换为 SQLite

* AI 模型已从 Claude 切换为 DeepSeek V4 Flash (via OpenRouter)

### 3.2 更新 `journey/design.md`

更新技术栈部分：

* 数据库：PostgreSQL 15+ → SQLite (aiosqlite)

* AI：Claude API → DeepSeek V4 Flash (via OpenRouter)

* 部署：移除 PostgreSQL 容器依赖

3.3 更新log文件夹 记录本次变更

***

## 四、执行步骤清单

1. `pyproject.toml` — 移除 `asyncpg`、`anthropic`，新增 `aiosqlite`、`openai`
2. `uv sync` — 安装新依赖
3. `app/config.py` — 更新 DATABASE\_URL、替换 CLAUDE\_API\_KEY 为 AI\_API\_KEY/AI\_BASE\_URL/AI\_MODEL
4. `app/database.py` — SQLite 引擎配置（check\_same\_thread、foreign\_keys pragma）
5. 9 个模型文件 — `UUID` → `Uuid`，`JSONB` → `JSON`
6. `alembic.ini` — 更新 sqlalchemy.url
7. `alembic/env.py` — 添加 `render_as_batch=True`
8. `app/services/ai_service.py` — 从 Anthropic SDK 切换到 OpenAI SDK + OpenRouter
9. `docker/docker-compose.yml` — 移除 PostgreSQL 服务，简化部署
10. `AGENTS.md` — 记录变更
11. `journey/design.md` — 更新技术栈快照
12. 运行 `uv run ruff check .` 和 `uv run mypy app/` 验证代码
13. 运行 `uv run pytest` 验证测试通过

