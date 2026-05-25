# 2026-05-20 技术栈迁移：PostgreSQL → SQLite + Claude → DeepSeek

## 变更概述

将项目从 PostgreSQL + Claude 技术栈迁移到 SQLite + DeepSeek V4 Flash (OpenRouter) 技术栈。

## 变更详情

### 数据库：PostgreSQL → SQLite
- **依赖**: `asyncpg` → `aiosqlite`
- **连接字符串**: `postgresql+asyncpg://...` → `sqlite+aiosqlite:///./intent_money.db`
- **引擎配置**: 添加 `connect_args={"check_same_thread": False}` 和 `PRAGMA foreign_keys=ON`
- **模型类型**: `UUID` (postgresql dialect) → `Uuid` (SQLAlchemy 内置), `JSONB` → `JSON`
- **Alembic**: 启用 `render_as_batch=True` 兼容 SQLite 的 ALTER TABLE 限制
- **Docker Compose**: 移除 PostgreSQL 容器，SQLite 数据库文件通过 volume 持久化

### AI 模型：Claude → DeepSeek V4 Flash
- **依赖**: `anthropic` → `openai`
- **SDK**: `Anthropic` (同步) → `AsyncOpenAI` (原生异步)
- **API 调用**: `client.messages.create()` → `client.chat.completions.create()`
- **配置项**: `CLAUDE_API_KEY` → `AI_API_KEY` + `AI_BASE_URL` + `AI_MODEL`
- **默认模型**: `deepseek/deepseek-chat-v3-0324:free` (via OpenRouter)

### 受影响文件
- `backend/pyproject.toml`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models/` (全部 9 个模型文件)
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/app/services/ai_service.py`
- `docker/docker-compose.yml`
- `AGENTS.md`
- `journey/design.md`

## 决策理由
- SQLite 简化部署，MVP 阶段无需独立数据库服务
- DeepSeek V4 Flash via OpenRouter 成本更低，支持 OpenAI SDK 兼容接口
- AsyncOpenAI 原生异步，无需 `asyncio.to_thread` 包装
