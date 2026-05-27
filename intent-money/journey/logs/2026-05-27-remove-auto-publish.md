# 2026-05-27 移除自动发布按钮 UI 变更

## 变更背景
简化任务详情页的操作流程，移除自动发布功能入口，统一使用手动复制发布流程。

## 具体变更

### 1. UI 调整
- **移除**："自动发布"按钮
- **修改**："确认已发放" → "请手动复制发布"
- **布局调整**：将主按钮与"换一条"按钮放在同一行
- **移除**：手动发布提示文字（`.manual-publish-hint`）

### 2. 修改前 UI 结构
```
.task-actions
├── CyberButton (确认已发放) - block 全宽
├── .manual-publish-hint (提示文字)
└── .action-row
    ├── CyberButton (自动发布)
    └── CyberButton (换一条)
```

### 3. 修改后 UI 结构
```
.task-actions
└── .action-row
    ├── CyberButton (请手动复制发布) - 主要按钮
    └── CyberButton (换一条) - 次要按钮
```

### 4. 代码修改位置
- 文件：`frontend/src/views/TaskDetail.vue`
- 行号：第 178-192 行（模板部分）

### 5. 旧代码
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

### 6. 新代码
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

## 影响分析
- 用户体验：简化操作流程，减少选择困惑
- 功能：移除自动发布功能入口，仅保留手动发布确认
- 数据追踪：`publish_clicked` 事件将不再记录 `mode: 'auto'`

## 相关文件
- `intent-money/frontend/src/views/TaskDetail.vue`
