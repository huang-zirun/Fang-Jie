# 小红书生成失败修复 - 2026-05-28

## 现象

用户在"选择平台界面"点击"小红书"后，显示"生成失败，请重试"。

## 根因

**Bug:** `content_tasks` 数据库表缺少 `deployed_at` 列。

- `ContentTask` 模型（`app/models/content_task.py`）定义了 `deployed_at: Mapped[datetime | None]` 字段
- 但 SQLite 数据库表 `content_tasks` 中没有该列（迁移遗漏）
- 创建任务时调用链：`create_task` → `generate_task` → 检查 `HAS_PENDING_TASK` → 查询 `content_tasks` 表
- SQLAlchemy 生成的 SQL 包含 `deployed_at` 列 → `sqlite3.OperationalError: no such column: content_tasks.deployed_at` → 500 错误

## 错误链路

```
用户点击小红书
  ↓
前端调用 POST /api/v1/tasks
  ↓
后端 generate_task 函数
  ↓
检查是否有未完成任务（HAS_PENDING_TASK）
  ↓
查询 content_tasks 表（包含 deployed_at 字段）
  ↓
SQLite 报错: no such column: content_tasks.deployed_at
  ↓
返回 500 错误
  ↓
前端显示"生成失败，请重试"
```

## 修复

```sql
ALTER TABLE content_tasks ADD COLUMN deployed_at DATETIME
```

## 验证

- `POST /api/v1/tasks`（小红书）→ 200，返回完整任务数据
- 小红书任务创建成功，包含小红书风格的内容结构

## 教训

- 修改 SQLAlchemy 模型后，必须同步更新 SQLite 数据库表结构（ALTER TABLE）
- SQLite 没有自动迁移机制，新增列必须手动执行 DDL
- 建议后续引入 Alembic 做正式的数据库版本管理