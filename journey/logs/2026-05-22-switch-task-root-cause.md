# 换一条失败根因排查日志

## 现象
点击任务详情页“换一条”失败。

## 根因
1. 后端 `POST /api/v1/tasks/{task_id}/swap` 在 SQLite 环境下会把 `content_tasks.created_at` 读成 naive datetime，但代码用 `datetime.now(timezone.utc)` 生成 aware datetime 后在 Python 层比较，触发 `TypeError: can't compare offset-naive and offset-aware datetimes`，表现为换条接口 500。
2. 任务详情页进入 `/task/:id` 后没有按 URL 中的任务 ID 拉取任务，而是调用 `/tasks/current`。当用户存在多个平台任务或最新任务不是 URL 指定任务时，页面上的“换一条”会操作错误任务，放大失败和平台混淆问题。

## 修复
- 新增 `app/utils/time.py`，统一 SQLite 下的 UTC naive 时间生成。
- `swap`、任务生成限流、发布确认、自动发布、过期清理统一使用该时间工具，避免 mixed timezone 比较。
- 后端新增 `GET /api/v1/tasks/{task_id}`，任务详情页改为按 route task id 加载。
- 新增 `backend/tests/test_task_swap.py`，覆盖 SQLite naive datetime 下的 pending 检查和 swap 直接调用。

## 验证
- `uv run pytest`：12 passed
- `npm run build`：通过
- `uv run python -m compileall app`：通过
