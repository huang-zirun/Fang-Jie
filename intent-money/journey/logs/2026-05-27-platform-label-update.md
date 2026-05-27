# 2026-05-27 平台名称标注更新

## 变更内容

为平台选择页面的平台名称添加类型标注，帮助用户更清晰地理解各平台的内容形式。

### 修改前
- 抖音 - 短视频平台，适合引流和成交
- 小红书 - 种草社区，适合IP打造和裂变

### 修改后
- 抖音（短视频）- 短视频平台，适合引流和成交
- 小红书（图文）- 种草社区，适合IP打造和裂变

## 技术实现

### 1. 修改种子数据
修改文件：`backend/app/seed.py`

```python
# 修改前
platforms = [
    Platform(id=PLATFORM_ID_DOUYIN, name="抖音", is_active=True),
    Platform(id=PLATFORM_ID_XIAOHONGSHU, name="小红书", is_active=True),
]

# 修改后
platforms = [
    Platform(id=PLATFORM_ID_DOUYIN, name="抖音（短视频）", is_active=True),
    Platform(id=PLATFORM_ID_XIAOHONGSHU, name="小红书（图文）", is_active=True),
]
```

### 2. 更新现有数据库数据
执行 SQL 更新语句：
```sql
UPDATE platforms SET name = '抖音（短视频）' WHERE name = '抖音';
UPDATE platforms SET name = '小红书（图文）' WHERE name = '小红书';
```

### 3. 修复 PlatformIcon 组件匹配逻辑
修改文件：`frontend/src/components/PlatformIcon.vue`

由于平台名称从"抖音"变为"抖音（短视频）"，原有的精确匹配逻辑失效，导致 Logo 无法显示。

```vue
<!-- 修改前 -->
v-if="platform === 'douyin' || platform === '抖音'"
v-else-if="platform === 'xiaohongshu' || platform === '小红书'"

<!-- 修改后 -->
v-if="platform === 'douyin' || platform.includes('抖音')"
v-else-if="platform === 'xiaohongshu' || platform.includes('小红书')"
```

使用 `includes` 方法可以兼容原始名称和带标注的名称。

## 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---------|---------|------|
| `backend/app/seed.py` | 修改 | 更新平台种子数据名称 |
| `frontend/src/components/PlatformIcon.vue` | 修改 | 修复 Logo 匹配逻辑 |
| `intent_money.db` | 数据更新 | 执行 SQL 更新现有平台名称 |

## 相关文件

- `frontend/src/views/PlatformSelect.vue` - 平台选择页面
