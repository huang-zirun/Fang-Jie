# 弹窗颜色不明显问题修复计划

## 问题描述
在深色主题下，Vant 弹窗（Dialog/ConfirmDialog）颜色不明显，与背景融为一体，用户难以识别弹窗边界和内容。

从截图可以看到：
- 弹窗背景色与页面背景色对比度不足
- 弹窗边框几乎看不见
- 按钮样式在深色背景下不够突出

## 影响范围
所有使用 Vant 弹窗的位置：
1. `TaskDetail.vue` - 4 处使用 `showConfirmDialog`：
   - L308: 确认已发放对话框
   - L349: 自动发布失败降级对话框
   - L369: 自动发布失败手动确认对话框
   - L398: 换一条确认对话框

2. `DataReport.vue` - 1 处使用 `showDialog`：
   - L263: 优化方案确认对话框

## 根因分析
`global.css` 中的 `.van-dialog` 样式定义：
```css
.van-dialog {
  background: var(--ink-charcoal) !important;  /* #1a1a2e - 与背景对比度不够 */
  border: 1px solid var(--border-cyan);        /* rgba(0,245,212,0.2) - 透明度太高 */
}
```

- `--ink-charcoal` (#1a1a2e) 与 `--ink-black` (#0a0a0f) 对比度不足
- `--border-cyan` 透明度只有 20%，几乎看不见
- 缺少弹窗阴影效果，无法形成视觉层次

## 修复方案

### 1. 增强弹窗样式 (`global.css`)

修改 `.van-dialog` 相关样式：

```css
.van-dialog {
  background: var(--ink-charcoal) !important;
  border: 1px solid rgba(0, 245, 212, 0.4);  /* 提高边框透明度 0.2 -> 0.4 */
  box-shadow: 
    0 0 0 1px rgba(0, 245, 212, 0.1),        /* 内发光 */
    0 8px 32px rgba(0, 0, 0, 0.6),           /* 外阴影 */
    0 0 40px rgba(0, 245, 212, 0.08);        /* 青色光晕 */
}

.van-dialog__header {
  color: var(--paper-white) !important;
  font-weight: 600;
  padding-top: 24px;
}

.van-dialog__message {
  color: var(--paper-dim) !important;         /* 使用更亮的文字色 */
  line-height: 1.6;
}

/* 按钮样式增强 */
.van-dialog__confirm {
  background: var(--gradient-btn-primary) !important;
  color: white !important;
  font-weight: 500;
}

.van-dialog__cancel {
  background: rgba(255, 255, 255, 0.05) !important;
  color: var(--paper-white) !important;
  border: 1px solid var(--border-gray);
}
```

### 2. 添加遮罩层样式

```css
.van-overlay {
  background: rgba(0, 0, 0, 0.7) !important;  /* 加深遮罩 */
  backdrop-filter: blur(2px);                  /* 轻微模糊效果 */
}
```

## 实施步骤

1. **修改 `global.css`** - 更新 `.van-dialog` 和 `.van-overlay` 样式
2. **验证修复效果** - 检查所有弹窗位置
3. **更新 journey 文档** - 记录修复内容

## 预期效果
- 弹窗边框更明显（透明度 0.4）
- 添加多层阴影形成视觉层次
- 遮罩层加深，突出弹窗内容
- 按钮样式更清晰可辨
