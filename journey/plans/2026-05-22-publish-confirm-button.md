# 发布确认按钮修复计划

## 背景
用户在首页选择意图、选择平台、复制话术后，找不到把任务状态标记为已发放/已发布的入口。

## 判断
- 后端已有 `POST /api/v1/tasks/{id}/publish`，会把任务状态从 `PENDING` 改为 `PUBLISHED`。
- 前端任务详情页已有发布逻辑，但入口文案偏向“自动发布”，不适合手动复制发布后的确认动作。
- `TaskOut` 当前没有返回 `status/published_at`，任务详情页依赖 `task.status` 显示底部操作，存在按钮不显示或状态不可靠的问题。

## 实施
1. 后端 `TaskOut` 增加 `status` 和 `published_at`，`_build_task_out()` 返回对应字段。
2. 前端任务详情页在 `PENDING` 状态显示“确认已发放”按钮，直接调用 `publishTask()`。
3. 保留自动发布入口，作为次级“自动发布”操作。
4. 补齐前端 `.vue` 与 `tracker.js` 类型声明，让构建可通过。

## 验证
- `uv run pytest`
- `npm run build`
