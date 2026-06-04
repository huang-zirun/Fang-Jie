# Alembic 迁移同步修复

## 日期
2026-06-04

## 问题背景
生产环境部署（`trades.zzy88.com`）时曾出现 Alembic 迁移异常。经全面排查，发现 SQLAlchemy 模型定义与 Alembic 迁移文件存在多处不一致，同时部署配置也存在隐患。这些差异在服务器从头构建数据库时会暴露为运行时错误。

## 发现的问题

### P0 - 严重
1. **`users` 表列不匹配**: 迁移有 `is_active`，模型有 `is_anonymous` + `updated_at`，运行时必报错
2. **`intents` 表缺 `sort_order` 列**: 模型有但迁移中不存在，涉及排序的查询会失败
3. **Docker 中 Alembic 使用错误数据库路径**: `env.py` 读取 `alembic.ini` 硬编码的 `./intent_money.db`，而非 Docker 环境变量 `DATABASE_URL` 指定的 `/app/data/intent_money.db`

### P1 - 高
4. **`intents.description` nullable 不匹配**: 模型 `nullable=False`，迁移 `nullable=True`
5. **`intents.is_active` 默认值矛盾**: 模型 `default=False`，迁移 `server_default='1'` (True)
6. **`diagnosis_results.task_id` 缺外键**: 级联删除不工作
7. **`user_events.user_id` 缺外键**: SET NULL 不工作

### P2 - 中
8. **`platforms.name` 长度不一致**: 模型 20，迁移 50
9. **`platforms` 缺 `created_at`**: 模型未声明但迁移有
10. **`user_platform_accounts` NOT NULL 列缺 server_default**

### 部署配置问题
11. **`entrypoint.sh` 无错误处理**: 迁移失败后应用仍启动
12. **`env.py` 未读取 `DATABASE_URL`**

## 修复方案

### 1. env.py — 支持 DATABASE_URL 环境变量
```python
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)
```

### 2. entrypoint.sh — 错误处理
- 添加 `set -e`：迁移失败时阻止应用启动
- 使用 `exec` 替换进程

### 3. 模型修复
- **platform.py**: `name` → `String(50)` + `unique=True`，补充 `created_at`
- **intent.py**: `description` → `nullable=True`，`name` → `unique=True`，`is_active` 修正 `server_default="1"`，`sort_order` 添加 `server_default="0"`
- **user_platform_account.py**: `cookie_status`/`bind_status` 添加 `server_default`

### 4. 新迁移 `a1b2c3d4e5f6`
- `users`: 删除 `is_active`，添加 `is_anonymous` + `updated_at`
- `intents`: 添加 `sort_order`，修正 `description` nullable/`is_active` server_default，添加 `name` 唯一约束
- `platforms`: 添加 `created_at`，添加 `name` 唯一约束
- `diagnosis_results`: 添加 `task_id` 外键 (CASCADE)
- `user_events`: 添加 `user_id` 外键 (SET NULL)
- `user_platform_accounts`: 添加 `cookie_status`/`bind_status` 的 server_default

### 5. SQLite PRAGMA foreign_keys 策略调整
- **不在 Alembic 迁移中启用**: SQLite `batch_alter_table` 模式（DROP + RECREATE）与 `PRAGMA foreign_keys=ON` 冲突，会导致迁移失败
- **仅在应用层连接时启用**: `database.py` 的 `connect` 事件中已有 `PRAGMA foreign_keys=ON`

## 变更文件清单

| 文件 | 变更 |
|------|------|
| `alembic/env.py` | 添加 `DATABASE_URL` 环境变量覆盖逻辑 |
| `entrypoint.sh` | 添加 `set -e` 和 `exec` |
| `app/models/platform.py` | 补充 `created_at`，`name` → `String(50)` + `unique=True` |
| `app/models/intent.py` | 修正 `nullable`/`server_default`/`unique` |
| `app/models/user_platform_account.py` | 添加 `server_default` |
| `alembic/versions/a1b2c3d4e5f6_sync_models_with_migrations.py` | 新迁移，同步所有差异 |

## 验证结果

在临时数据库上从头运行完整迁移链验证：
```bash
$ DATABASE_URL=sqlite+aiosqlite:///./test_migration.db uv run alembic upgrade head
# Running upgrade  -> 000000000000 (initial)
# Running upgrade 000000000000 -> 6447982821b9 (add_user_platform_accounts_table)
# Running upgrade 6447982821b9 -> a1b2c3d4e5f6 (sync models with migrations)
```

验证所有 15 张表结构、外键约束、唯一约束均与模型定义一致。

## 后续注意
- 服务器部署时执行 `docker compose up -d --build` 即可自动应用迁移
- 本地开发数据库（`intent_money.db`）已用 `alembic stamp a1b2c3d4e5f6` 标记为新 head（因之前通过 `create_all()` 直接创建，结构已是最新）
- 未来修改模型后，必须同步生成 Alembic 迁移并验证，避免出现同样的问题
