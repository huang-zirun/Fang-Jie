# 2026-05-26 弹窗 UI 全面优化

## 问题汇总

本次修复解决了深色主题下所有弹窗的显示问题：

1. **弹窗颜色不明显** - Dialog/ConfirmDialog 与背景融为一体
2. **弹窗内容拥挤** - 标题、内容、按钮之间没有足够的呼吸空间
3. **Loading Toast 白色背景** - 生成新任务时的加载弹窗是白色底

## 影响范围

### Dialog 弹窗（5 处）
- `TaskDetail.vue` - 4 处：`showConfirmDialog` 调用
- `DataReport.vue` - 1 处：`showDialog` 调用

### Loading Toast（5 处）
- `TaskDetail.vue` L320: "确认中..."
- `TaskDetail.vue` L338: "正在发布..."
- `TaskDetail.vue` L375: "确认中..."
- `TaskDetail.vue` L402: "生成新任务..."
- `DataReport.vue` L275: "生成优化任务..."

## 修复内容

### 修改文件
`frontend/src/styles/global.css`

### 1. Dialog 样式优化

```css
.van-dialog {
  background: var(--ink-charcoal) !important;
  border: 1px solid rgba(0, 245, 212, 0.4);
  box-shadow:
    0 0 0 1px rgba(0, 245, 212, 0.1),
    0 8px 32px rgba(0, 0, 0, 0.6),
    0 0 40px rgba(0, 245, 212, 0.08);
  border-radius: 20px !important;
}

.van-dialog__header {
  color: var(--paper-white) !important;
  font-weight: 600;
  font-size: 18px;
  padding: 28px 28px 12px;
}

.van-dialog__content {
  padding: 0 28px;
}

.van-dialog__message {
  color: var(--paper-dim) !important;
  line-height: 1.7;
  font-size: 15px;
  padding: 8px 0 4px;
}

.van-dialog__footer {
  padding: 20px 28px 28px;
  display: flex;
  gap: 12px;
}

.van-dialog__footer button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-size: 15px;
}

.van-dialog__confirm {
  background: var(--gradient-btn-primary) !important;
  color: white !important;
  font-weight: 500;
  border: none !important;
}

.van-dialog__cancel {
  background: rgba(255, 255, 255, 0.05) !important;
  color: var(--paper-white) !important;
  border: 1px solid var(--border-gray) !important;
}
```

### 2. Toast 样式优化

```css
.van-toast {
  background: var(--ink-charcoal) !important;
  border: 1px solid var(--border-cyan);
  box-shadow:
    0 0 0 1px rgba(0, 245, 212, 0.1),
    0 8px 32px rgba(0, 0, 0, 0.6),
    0 0 40px rgba(0, 245, 212, 0.08);
  border-radius: 16px !important;
  padding: 24px 32px !important;
}

.van-toast--loading {
  background: var(--ink-charcoal) !important;
}

.van-toast__loading {
  color: var(--neon-cyan) !important;
}

.van-toast__text {
  color: var(--paper-white) !important;
  font-size: 15px !important;
  margin-top: 12px !important;
}
```

### 3. 遮罩层优化

```css
.van-overlay {
  background: rgba(0, 0, 0, 0.7) !important;
  backdrop-filter: blur(2px);
}
```

## 优化要点

| 优化项 | 改动前 | 改动后 |
|--------|--------|--------|
| 边框透明度 | 0.2 | 0.4 |
| 圆角 | 16px | 20px (Dialog) / 16px (Toast) |
| 标题内边距 | 默认 | 28px 28px 12px |
| 内容区边距 | 默认 | 0 28px |
| 底部内边距 | 默认 | 20px 28px 28px |
| 按钮高度 | 默认 | 44px |
| 按钮间距 | 默认 | 12px |
| 遮罩透明度 | 默认 | 0.7 + 模糊 |

## 预期效果

- **Dialog**: 边框更明显，视觉层次清晰，内容宽敞舒适，按钮易点击
- **Toast**: 深色背景与主题一致，青色边框和阴影使弹窗更明显
- **遮罩层**: 加深并添加模糊效果，突出弹窗内容

## 相关文件

- `frontend/src/styles/global.css` - 样式定义
- `frontend/src/views/TaskDetail.vue` - Dialog/Toast 调用
- `frontend/src/views/DataReport.vue` - Dialog/Toast 调用
