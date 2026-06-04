# 投放追踪与持续性数据更新

> 日期: 2026-05-27
> 状态: DRAFT

## 背景与问题

内容发布后，效果需要时间积累（播放量、评论数、私信数会持续增长）。当前系统存在以下限制：

1. **PerformanceReport 与 ContentTask 是一对一关系**（`task_id` unique 约束），只能记录一次快照，无法追踪数据随时间的变化趋势
2. **没有投放日期字段**：`published_at` 记录的是系统标记发布的时间，但实际投放（内容上线对用户可见）的时间可能不同
3. **数据上报仅支持手动填写**，无法自动从平台抓取
4. **诊断只能触发一次**，无法基于持续积累的数据重新诊断

## 需求总结

| 维度 | 决策 |
|------|------|
| 数据模型 | 新增时间序列快照表，保留现有 PerformanceReport 不变 |
| 数据来源 | 手动填写 + CDP 自动抓取，两者结合 |
| 抓取时机 | 用户手动触发 + 后台定时任务兜底 |
| 指标范围 | 维持现有三个：播放量、评论数、私信数 |
| 投放日期 | 新增 `deployed_at` 字段，与 `published_at` 分离 |
| 诊断触发 | 用户手动触发，综合所有快照数据分析 |

## 数据模型变更

### 1. ContentTask 新增字段

```python
# content_task.py
deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- `published_at`：系统标记「已发布」的时间（用户点击发布按钮的时间）
- `deployed_at`：实际投放日期（内容上线对用户可见的时间），由用户手动设置或自动抓取确认

### 2. 新增 PerformanceSnapshot 表

```python
class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("content_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    # source: "manual" | "cdp_auto" | "cdp_manual"
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("ContentTask", back_populates="snapshots")
```

**设计要点**：
- 同一个 task 可以有多条 snapshot，形成时间序列
- `source` 字段区分数据来源（手动 / CDP 自动抓取 / CDP 手动触发）
- `snapshot_at` 记录快照时间，用于计算「发布后第 N 天」和趋势分析
- 保留现有 `PerformanceReport` 不变，避免影响已有的诊断流程

### 3. ContentTask 新增 relationship

```python
snapshots = relationship("PerformanceSnapshot", back_populates="task", order_by="PerformanceSnapshot.snapshot_at", lazy="selectin")
```

## API 变更

### 新增接口

#### POST /tasks/{task_id}/snapshots — 上报数据快照

手动填写数据时调用。

```json
// Request Body
{
  "play_count": 1200,
  "comment_count": 35,
  "message_count": 8
}

// Response
{
  "id": "uuid",
  "task_id": "uuid",
  "play_count": 1200,
  "comment_count": 35,
  "message_count": 8,
  "source": "manual",
  "snapshot_at": "2026-05-27T10:00:00Z"
}
```

**前置条件**：task 状态为 `PUBLISHED`

#### GET /tasks/{task_id}/snapshots — 获取快照列表

返回某个 task 的所有快照，按时间排序。

```json
// Response
[
  {
    "id": "uuid",
    "play_count": 500,
    "comment_count": 10,
    "message_count": 2,
    "source": "manual",
    "snapshot_at": "2026-05-25T10:00:00Z"
  },
  {
    "id": "uuid",
    "play_count": 1200,
    "comment_count": 35,
    "message_count": 8,
    "source": "cdp_auto",
    "snapshot_at": "2026-05-27T10:00:00Z"
  }
]
```

#### POST /tasks/{task_id}/snapshots/fetch — 手动触发 CDP 抓取

用户点击「刷新数据」时调用，通过 CDP 从平台创作者后台抓取最新数据。

```json
// Response
{
  "id": "uuid",
  "task_id": "uuid",
  "play_count": 3500,
  "comment_count": 80,
  "message_count": 15,
  "source": "cdp_manual",
  "snapshot_at": "2026-05-27T14:30:00Z"
}
```

**前置条件**：task 状态为 `PUBLISHED`，CDP 可用

#### PATCH /tasks/{task_id}/deploy — 设置投放日期

```json
// Request Body
{
  "deployed_at": "2026-05-25T08:00:00Z"
}

// Response
{
  "task_id": "uuid",
  "deployed_at": "2026-05-25T08:00:00Z"
}
```

#### POST /tasks/{task_id}/diagnose — 手动触发诊断（综合所有快照）

替代现有的「上报即诊断」流程。诊断时综合所有快照数据分析趋势。

```json
// Response
{
  "diagnosis": {
    "problem_type": "low_play",
    "problem_desc": "播放量增长缓慢",
    "optimization_direction": "优化钩子前3秒",
    "optimization_detail": "...",
    "ai_analysis": "...",
    "rule_confidence": 0.85,
    "snapshot_summary": {
      "total_snapshots": 3,
      "days_since_deploy": 2,
      "play_trend": "slow_growth",
      "latest_play_count": 3500,
      "avg_daily_play_growth": 1200
    }
  }
}
```

**前置条件**：task 状态为 `PUBLISHED`，至少有 1 条快照

### 修改现有接口

#### POST /tasks/{task_id}/publish — 发布时可选设置投放日期

Request Body 新增可选字段：

```json
{
  "deployed_at": "2026-05-25T08:00:00Z"  // 可选
}
```

#### GET /tasks/{task_id} & GET /tasks/current — 返回值新增字段

```json
{
  "deployed_at": "2026-05-25T08:00:00Z",
  "latest_snapshot": {
    "play_count": 3500,
    "comment_count": 80,
    "message_count": 15,
    "snapshot_at": "2026-05-27T14:30:00Z"
  },
  "snapshot_count": 3
}
```

#### GET /tasks/history — 返回值新增字段

```json
{
  "deployed_at": "2026-05-25T08:00:00Z",
  "latest_play_count": 3500,
  "latest_comment_count": 80,
  "latest_message_count": 15,
  "snapshot_count": 3
}
```

## 后台定时任务

### CDP 自动抓取定时任务

- **触发频率**：每 2 小时
- **抓取范围**：状态为 `PUBLISHED` 且 `deployed_at` 在 30 天内的任务
- **抓取逻辑**：通过 CDP 从平台创作者后台获取最新数据，写入 `performance_snapshots`（source=`cdp_auto`）
- **去重**：同一 task 在 1 小时内不重复抓取

### 实现方式

在 `app/services/` 下新增 `snapshot_scheduler.py`，使用 APScheduler 或 FastAPI lifespan 启动的 asyncio 后台任务。

## 诊断逻辑改造

现有 `diagnose_performance()` 只接收单个 `PerformanceReport`。需要改造为：

1. 接收 task_id，查询所有 `PerformanceSnapshot`
2. 计算趋势指标：
   - `days_since_deploy`：投放至今天数
   - `play_trend`：播放量增长趋势（slow_growth / steady / viral / declining）
   - `avg_daily_play_growth`：日均播放增长
   - `engagement_rate`：互动率（评论+私信 / 播放）
3. 将趋势指标 + 最新快照数据传给 AI 进行诊断
4. 诊断结果写入 `DiagnosisResult`，新增字段存储趋势摘要

### DiagnosisResult 新增字段

```python
snapshot_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
days_since_deploy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
play_trend: Mapped[str | None] = mapped_column(String(20), nullable=True)
avg_daily_play_growth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
```

## 状态流转变更

**现有**：
```
PENDING → PUBLISHED → REPORTED → DIAGNOSED
```

**新**：
```
PENDING → PUBLISHED → (持续上报快照) → DIAGNOSED
```

- 移除 `REPORTED` 状态（不再需要，因为快照是持续记录的）
- `PUBLISHED` 状态下可以多次上报快照
- 用户手动触发诊断后，状态变为 `DIAGNOSED`
- `DIAGNOSED` 后仍可继续上报快照，并可再次触发诊断（状态保持 `DIAGNOSED`，更新诊断结果）

## 数据库迁移

需要新增 Alembic migration：

1. `content_tasks` 表新增 `deployed_at` 列（nullable）
2. 新建 `performance_snapshots` 表
3. `diagnosis_results` 表新增 `snapshot_count`、`days_since_deploy`、`play_trend`、`avg_daily_play_growth` 列

## 兼容性考虑

- 现有 `PerformanceReport` 表和 `POST /tasks/{task_id}/report` 接口保留，标记为 deprecated
- 前端逐步迁移到新的快照接口
- 现有 `REPORTED` 状态的任务继续正常工作

## 实施步骤

1. 新增 `PerformanceSnapshot` 模型 + Alembic migration
2. ContentTask 新增 `deployed_at` 字段 + `snapshots` relationship
3. DiagnosisResult 新增趋势字段
4. 新增快照相关 API（CRUD + CDP 抓取）
5. 新增设置投放日期 API
6. 改造诊断逻辑（综合快照分析）
7. 新增后台定时抓取任务
8. 更新 TaskOut / TaskHistoryOut schema
9. 标记旧 report 接口为 deprecated
