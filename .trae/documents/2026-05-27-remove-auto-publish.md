# 移除自动发布按钮 UI 修改计划

## 需求概述
1. 移除"自动发布"按钮
2. 将"确认已发放"按钮文字改为"请手动复制发布"
3. 将"请手动复制发布"按钮与"换一条"按钮放在同一行

## 当前 UI 结构（PENDING 状态）

```
.task-actions
├── CyberButton (确认已发放) - block 全宽
├── .manual-publish-hint (提示文字)
└── .action-row
    ├── CyberButton (自动发布) - 需要移除
    └── CyberButton (换一条)
```

## 修改后 UI 结构

```
.task-actions
└── .action-row
    ├── CyberButton (请手动复制发布) - 占据主要空间
    └── CyberButton (换一条) - 次要按钮
```

## 具体修改步骤

### 1. 修改模板部分（TaskDetail.vue 第 178-192 行）

**当前代码：**
```vue
<template v-if="task?.status === 'PENDING'">
  <CyberButton variant="primary" size="large" block :loading="publishState === 'confirming'" @click="handleManualConfirm">
    确认已发放
  </CyberButton>
  <div class="manual-publish-hint">复制话术并发到平台后，点这里进入数据回填</div>
  <div class="action-row">
    <CyberButton variant="secondary" size="default" :loading="publishState === 'publishing'" @click="handlePublish">
      自动发布
    </CyberButton>
    <CyberButton variant="ghost" size="default" @click="handleSwap">
      换一条
    </CyberButton>
  </div>
</template>
```

**修改后代码：**
```vue
<template v-if="task?.status === 'PENDING'">
  <div class="action-row">
    <CyberButton variant="primary" size="large" :loading="publishState === 'confirming'" @click="handleManualConfirm">
      请手动复制发布
    </CyberButton>
    <CyberButton variant="ghost" size="default" @click="handleSwap">
      换一条
    </CyberButton>
  </div>
</template>
```

### 2. 移除相关样式（可选）

如果 `.manual-publish-hint` 样式不再需要，可以在 `<style>` 部分移除（第 733-738 行）：

```css
.manual-publish-hint {
  text-align: center;
  color: var(--ink-gray);
  font-size: 12px;
  line-height: 1.5;
}
```

### 3. 移除相关方法（可选清理）

`handlePublish` 方法（第 355-414 行）如果不再需要可以移除，但保留也无影响。

## 修改影响分析

| 项目 | 影响 |
|------|------|
| 用户体验 | 简化操作流程，减少选择困惑 |
| 功能 | 移除自动发布功能入口，仅保留手动发布确认 |
| 代码 | 删除约 5-10 行模板代码，可选清理相关方法和样式 |
| 数据追踪 | `publish_clicked` 事件将不再记录 `mode: 'auto'` |

## 实现文件

- `e:\系统文件夹\Desktop\Channing\Fang-Jie\intent-money\frontend\src\views\TaskDetail.vue`
