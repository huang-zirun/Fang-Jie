# 点击平台生成失败修复 - 2026-05-25

## 现象

前端点击任意平台（抖音/小红书）后，显示"生成失败，请重试"。
后端 `POST /api/v1/tasks` 返回 500 Internal Server Error。
当时 Chrome CDP 后端还挂着。

## 根因

**Bug #1（根因）：** `market_hots` 数据库表缺少 `comment_sentiment` 列。

- `MarketHot` 模型（`app/models/market_hot.py`）定义了 `comment_sentiment: Mapped[dict | None]` 字段
- 但 SQLite 数据库表 `market_hots` 中没有该列（迁移遗漏）
- 创建任务时调用链：`create_task` → `generate_task` → `match_content_structure()` → 查询 `market_hots` 表
- SQLAlchemy 生成的 SQL 包含 `comment_sentiment` 列 → `sqlite3.OperationalError: no such column: market_hots.comment_sentiment` → 500

**Bug #2（次要）：** `platforms` 表和模型缺少 `description` 字段。

- 前端 `PlatformSelect.vue` 显示 `platform.description`，但该字段在数据库和模型中均不存在
- 导致平台上无描述文字显示

## 修复

### Bug #1

```sql
ALTER TABLE market_hots ADD COLUMN comment_sentiment JSON
```

### Bug #2

1. 数据库迁移：
```sql
ALTER TABLE platforms ADD COLUMN description VARCHAR(200)
UPDATE platforms SET description='短视频平台，适合引流和成交' WHERE name LIKE '%抖音%'
UPDATE platforms SET description='种草社区，适合IP打造和裂变' WHERE name LIKE '%小红书%'
```

2. 模型 `app/models/platform.py` — 新增字段：
```python
description: Mapped[str | None] = mapped_column(String(200), nullable=True)
```

3. API `app/api/v1/intents.py` — `get_platforms` 返回值加入 `description`：
```python
{"id": str(p.id), "name": p.name, "description": p.description or "", "is_active": p.is_active}
```

## 验证

- `POST /api/v1/tasks`（抖音）→ 200，返回完整任务数据（hook_text / storyboard / script_text / title 等）
- `POST /api/v1/tasks`（小红书）→ 200，返回完整任务数据
- `GET /api/v1/platforms` → 200，每个平台包含 `description` 字段
- 前端点击平台 → 正常跳转至任务详情页，不再显示"生成失败"

## 教训

- 修改 SQLAlchemy 模型后，必须同步更新 SQLite 数据库表结构（ALTER TABLE）
- SQLite 没有自动迁移机制，新增列必须手动执行 DDL
- 建议后续引入 Alembic 做正式的数据库版本管理
