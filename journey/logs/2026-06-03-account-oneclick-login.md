# 账号管理页面简化：一键登录 + 扩展调起

> 日期: 2026-06-03
> 状态: DONE

## 背景

账号管理页面原有 3 个操作按钮：导入Cookie、获取Cookie、一键登录（或扫码登录）。用户希望进一步简化，去掉手动导入和获取Cookie，只保留"一键登录"，且点击后能调起浏览器扩展。

## 改动

### 1. 前端 UI 简化 (AccountManage.vue)

- **移除**：
  - "导入Cookie"按钮及对应的导入对话框 (`cookieDialogVisible`, `cookieForm`, `openCookieDialog`, `handleImportCookie`)
  - "获取Cookie"按钮 (`handleFetchCookies` 仍保留，仅用于"同步到后端"条件按钮)
- **保留**：
  - "一键登录"（主按钮）
  - "同步到后端"（扩展已登录但后端未绑定时显示）
  - "验证"、"解绑"

### 2. 一键登录逻辑 (`handleOneClickLogin`)

按优先级自动选择路径：

```
未安装扩展 → 扫码登录 (startQrLogin)
扩展已安装 + 浏览器已登录 → 直接同步 cookie (extensionLogin)
扩展已安装 + 浏览器未登录 → 尝试调起扩展 popup (extensionTriggerPopup)
                                    ↓
                           调起成功 → 提示"已调起扩展，请在扩展中完成登录"
                           调起失败 → fallback 打开平台登录页 (extensionGuidedLogin)
```

### 3. 扩展通信协议新增

| 方向 | 消息类型 | 说明 |
|------|----------|------|
| 前端 → content script | `INTENT_MONEY_TRIGGER_POPUP` | 请求调起扩展 popup |
| content script → background | `TRIGGER_POPUP` | 转发调起请求 |
| background | `chrome.action.openPopup()` | 尝试打开 popup |
| content script → 前端 | `INTENT_MONEY_TRIGGER_POPUP_RESULT` | 返回调起结果 |

### 4. 扩展端改动

- **content.js**：新增 `INTENT_MONEY_TRIGGER_POPUP` handler，转发给 background
- **background.js**：新增 `TRIGGER_POPUP` handler，尝试调用 `chrome.action.openPopup()`

## 已知限制

- `chrome.action.openPopup()` 在部分浏览器/版本上受限（通常只允许在用户直接点击扩展图标后的短窗口期内调用）。如果调起失败，会自动 fallback 到打开平台登录页，用户仍可在新标签页完成登录，扩展后台会监听 `chrome.cookies.onChanged` 自动同步。
- 扩展 popup 被调起后，用户需手动点击"获取Cookie并同步"或"打开登录页"完成操作。登录成功后，background 会自动广播 `STATUS_UPDATE` 到前端，前端刷新账号列表。
