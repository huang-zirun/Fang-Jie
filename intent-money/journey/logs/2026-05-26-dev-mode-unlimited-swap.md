# 开发模式无限换条功能

## 需求
开发/测试模式下移除"换一条"的每日1次限制，方便开发和测试。

## 实现方案
通过环境变量 `DEV_MODE` 控制，开启后跳过换条次数限制检查。

## 修改文件

### 1. backend/app/config.py
添加 `DEV_MODE` 配置项：
```python
DEV_MODE: bool = False  # 开发模式开关，开启后无限换条
```

### 2. backend/app/api/v1/tasks.py
- 导入 settings
- 修改 `swap_task` 函数限制逻辑：
```python
if not settings.DEV_MODE and swap_count_today >= 1:
    raise HTTPException(...)
```

### 3. 修复 swap_task 异常处理问题（2026-05-26 追加）
**问题**：换条时显示"换条失败"，无详细错误信息

**原因**：
1. 删除旧任务后未立即提交，导致 `generate_task` 查询时仍能看到已删除任务
2. 异常捕获不完整，未捕获非 ValueError 异常

**修复内容**：
```python
# 修复1：删除后立即提交
await db.delete(task)
await db.commit()  # 新增

# 修复2：添加通用异常捕获
try:
    new_task = await generate_task(...)
    ...
except ValueError as e:
    ...
except Exception as e:  # 新增
    raise HTTPException(status_code=500, detail=f"换条失败: {str(e)}")
```

## 使用方法
在 `.env` 文件中设置：
```bash
DEV_MODE=true
```

## 影响范围
- 仅影响 `POST /api/v1/tasks/{task_id}/swap` 接口
- 向后兼容，不修改数据库结构
- 生产环境保持默认 `false` 即可维持原有约束
