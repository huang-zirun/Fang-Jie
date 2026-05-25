# 2026-05-22 平台 Logo 修复与任务系统架构修复

## 问题背景

用户报告三个问题：
1. 平台选择页面的抖音和小红书显示通用手机图标，需要换成对应平台 logo
2. 点击小红书进入任务详情页，显示的是抖音的任务信息
3. 点击小红书失败，抖音成功

## 根本原因分析

### 问题 1：Logo 显示不正确
- **原因**：后端 `Platform` 模型没有 `code` 字段，只有 `name` 字段（"抖音"/"小红书"）
- **原代码**：前端使用 `platform.code` 匹配图标，但后端返回的是 `platform.name`

### 问题 2：小红书显示抖音任务（平台混淆）
- **根本原因**：[tasks.py:160](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/tasks.py#L160) 在处理 `HAS_PENDING_TASK` 错误时：
  ```python
  existing = await get_current_task(db, current_user.id)  # 缺少 platform_id 参数！
  ```
- **后果**：返回的是任意平台的最新未完成任务，而不是当前请求平台的任务
- **流程**：
  1. 用户点击小红书 → 传入小红书 platform_id
  2. 后端检查到小红书有未完成任务 → 抛出 HAS_PENDING_TASK
  3. 但获取任务时没有传入 platform_id → 返回抖音的任务
  4. 前端显示抖音任务，用户困惑

### 问题 3：小红书创建任务失败
- **原因**：`generate_task` 函数检查所有平台的未完成任务，而不是仅检查当前平台
- **后果**：如果用户有抖音未完成任务，就无法创建小红书任务

## 修复方案

### 1. 平台 Logo 修复

**文件**：
- [PlatformIcon.vue](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/frontend/src/components/PlatformIcon.vue) - 新建组件
- [PlatformSelect.vue](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/frontend/src/views/PlatformSelect.vue)
- [douyin-logo.svg](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/frontend/src/assets/douyin-logo.svg) - 抖音音符图标
- [xiaohongshu-logo.svg](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/frontend/src/assets/xiaohongshu-logo.svg) - 小红书书本图标

**变更**：
- 创建 `PlatformIcon` 组件，根据 `platform.name` 匹配对应 SVG 图标
- 支持 "抖音" 和 "douyin" 两种格式匹配
- 下载官方 SVG logo 文件

### 2. 任务系统架构修复

**文件**：
- [task_service.py](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/task_service.py)
- [tasks.py](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/api/v1/tasks.py)
- [tasks.ts](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/frontend/src/api/tasks.ts)

**核心变更**：

1. **生成任务时按平台检查**（task_service.py:57-69）：
   ```python
   # 添加 platform_id 过滤
   ContentTask.platform_id == platform_id,
   ```

2. **获取当前任务时支持平台过滤**（task_service.py:172-179）：
   ```python
   async def get_current_task(db, user_id, platform_id=None):
       if platform_id:
           query = query.where(ContentTask.platform_id == platform_id)
   ```

3. **API 修复关键 bug**（tasks.py:160）：
   ```python
   # 修复前：existing = await get_current_task(db, current_user.id)
   # 修复后：
   existing = await get_current_task(db, current_user.id, data.platform_id)
   ```

4. **前端 API 更新**（tasks.ts:15-17）：
   ```typescript
   export function getCurrentTask(platformId?: string) {
     // 传入 platform_id 参数
   }
   ```

## 架构设计决策

### 决策：允许不同平台同时有未完成任务

**原因**：
- 用户可能同时在抖音和小红书运营账号
- 不同平台的内容策略不同，不应互相阻塞
- 符合"意图-平台"矩阵的业务模型

**实现**：
- 将 "每个用户一个未完成任务" 改为 "每个用户-平台组合一个未完成任务"
- 数据库查询添加 `platform_id` 过滤条件

## 验证结果

- [x] 抖音显示音符图标，小红书显示红色书本图标
- [x] 点击小红书正确显示小红书任务
- [x] 抖音和小红书可同时有未完成任务
- [x] 平台切换逻辑正确

## 相关文件

### 后端
- `backend/app/services/task_service.py`
- `backend/app/api/v1/tasks.py`

### 前端
- `frontend/src/components/PlatformIcon.vue`
- `frontend/src/views/PlatformSelect.vue`
- `frontend/src/api/tasks.ts`
- `frontend/src/assets/douyin-logo.svg`
- `frontend/src/assets/xiaohongshu-logo.svg`

## 经验教训

1. **API 设计原则**：当处理特定资源的错误时，必须携带该资源的标识符，不能依赖全局状态
2. **代码审查重点**：检查 "获取当前/最新" 类函数是否缺少必要的过滤参数
3. **测试覆盖**：需要测试多平台并发场景，确保平台隔离性
