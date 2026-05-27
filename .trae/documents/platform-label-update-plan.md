# 平台选择页面标注更新计划

## 需求描述

在平台选择页面中，为每个平台名称后面添加类型标注：

* 抖音 → 抖音（短视频）

* 小红书 → 小红书（图文）

## 当前状态

* 页面文件: `intent-money/frontend/src/views/PlatformSelect.vue`

* 平台数据从 API `/platforms` 获取，包含 `name` 和 `description` 字段

* 当前显示效果:

  * 抖音 - 短视频平台，适合引流和成交

  * 小红书 - 种草社区，适合IP打造和裂变

## 实现方案

### 方案1: 修改后端数据库（推荐）

修改 `backend/app/seed.py` 中的 `seed_platforms` 函数，在平台名称后添加类型标注。

**优点:**

* 数据层面统一，所有地方显示一致

* 实现简单直接

**修改位置:**

```python
# backend/app/seed.py 第41-44行
platforms = [
    Platform(id=PLATFORM_ID_DOUYIN, name="抖音（短视频）", is_active=True),
    Platform(id=PLATFORM_ID_XIAOHONGSHU, name="小红书（图文）", is_active=True),
]
```

### 方案2: 前端动态添加

修改 `PlatformSelect.vue`，在显示平台名称时动态添加类型标注。

**优点:**

* 不需要修改数据库

* 可以根据需要灵活调整显示格式

**修改位置:**

```vue
<!-- PlatformSelect.vue 第23行 -->
<div class="platform-name">{{ getPlatformDisplayName(platform.name) }}</div>
```

添加方法:

```typescript
const getPlatformDisplayName = (name: string): string => {
  if (name === '抖音') return '抖音（短视频）'
  if (name === '小红书') return '小红书（图文）'
  return name
}
```

## 采用方案1并把变更更新到jounery系统

考虑到这是一个持久性的产品需求，且平台类型是固定的，建议采用方案1，在数据库层面修改平台名称，这样所有使用平台名称的地方都会自动更新。

## 实施步骤

1. 修改 `backend/app/seed.py` 中的平台名称
2. （可选）如果数据库已有数据，需要更新现有数据或重新初始化

## 预期效果

* 抖音（短视频）- 短视频平台，适合引流和成交

* 小红书（图文）- 种草社区，适合IP打造和裂变

