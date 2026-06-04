# 同浏览器获取小红书 Cookie 方案调研 Spec

## Why
当前系统获取小红书 Cookie 依赖两种方式：(1) CDP 连接用户以 `--remote-debugging-port` 启动的 Chrome，(2) Playwright 启动独立 headless 浏览器。两者都需要额外配置或启动独立浏览器，用户体验差。用户希望直接在打开前端的同一浏览器中获取小红书 Cookie，实现零配置、无感登录。

## What Changes
- 调研并确定"同浏览器获取小红书 Cookie"的技术方案
- 核心挑战：**同源策略（Same-Origin Policy）** — 前端页面（如 `localhost:5173`）无法访问 `xiaohongshu.com` 域名的 Cookie，尤其是 `httpOnly` 的 `web_session` Cookie

## Impact
- Affected specs: multi-account-cookie-management, xhs-qrcode-login-validation-fix, fix-xhs-login-false-positive
- Affected code: `cdp_qrcode_login.py`, `qrcode_login.py`, `AccountManage.vue`, `accounts.ts`, `accounts.py`

---

## 调研分析

### 核心约束

| 约束 | 说明 |
|------|------|
| 同源策略 | 前端 JS 无法读取 `xiaohongshu.com` 的 Cookie |
| httpOnly | `web_session` 是 httpOnly Cookie，`document.cookie` 无法读取 |
| 跨域隔离 | Chrome 第三方 Cookie 限制（SameSite=None 也可能被拦截） |
| 反自动化 | 小红书有强反 headless 检测 |

### 小红书关键 Cookie 清单

| Cookie 名 | httpOnly | 用途 | 获取难度 |
|-----------|----------|------|---------|
| `web_session` | ✅ | 主会话凭证 | 必须用扩展/CDP |
| `a1` | ❌ | 设备标识 | `document.cookie` 可读 |
| `webId` | ❌ | 设备ID | `document.cookie` 可读 |
| `galaxy_creator_session_id` | ✅ | 创作者会话 | 必须用扩展/CDP |

---

## 方案对比

### 方案 A：Chrome 扩展（推荐 ⭐）

**原理**：开发一个 Chrome Extension，利用 `chrome.cookies` API 读取所有 Cookie（包括 httpOnly），通过 `window.postMessage` 或 HTTP API 传给前端/后端。

**流程**：
```
用户安装扩展 → 扩展 popup 显示"获取小红书 Cookie"按钮
  → 用户点击 → 扩展调用 chrome.cookies.getAll({domain: ".xiaohongshu.com"})
  → 获取完整 Cookie（含 httpOnly 的 web_session）
  → 通过 postMessage 发送给前端页面 / 直接 POST 到后端 API
  → 前端显示"登录成功" / 后端加密存储 Cookie
```

**增强流程（自动检测登录）**：
```
扩展 background script 监听 chrome.cookies.onChanged
  → 检测到 xiaohongshu.com 的 web_session 变化
  → 自动将新 Cookie 发送到后端
  → 前端通过 SSE/WebSocket 实时更新状态
```

**增强流程（引导登录）**：
```
用户点击"扫码登录" → 前端通过 postMessage 通知扩展
  → 扩展打开新标签页访问 xiaohongshu.com
  → 用户在小红书页面扫码登录
  → 扩展通过 chrome.tabs.onUpdated / chrome.cookies.onChanged 检测登录完成
  → 扩展提取 Cookie 并发送到后端
  → 前端收到通知，显示"登录成功"
```

| 维度 | 评价 |
|------|------|
| httpOnly Cookie | ✅ 可读取 |
| 用户体验 | ⭐⭐⭐⭐ 一次安装，后续无感 |
| 安全性 | ⭐⭐⭐⭐ 权限声明清晰，用户可控 |
| 部署复杂度 | ⭐⭐⭐ 需开发扩展，但代码量小 |
| 云部署兼容 | ✅ 完全兼容，不依赖本地 CDP |
| 反检测风险 | ✅ 无自动化特征 |
| Cookie 刷新 | ✅ 可监听 onChanged 自动续期 |

**技术要点**：
- `manifest.json` 声明 `"permissions": ["cookies", "tabs"]`，`"host_permissions": ["*://*.xiaohongshu.com/*"]`
- 使用 Manifest V3（Chrome 当前标准）
- `chrome.cookies.getAll({domain: ".xiaohongshu.com"})` 获取所有 Cookie
- 前端与扩展通信：`chrome.runtime.sendMessage` / `window.postMessage`
- 扩展与后端通信：直接 `fetch` 后端 API（需配置 CORS）

---

### 方案 B：CDP 增强（当前方案优化）

**原理**：优化现有 CDP 方案，降低用户配置门槛。

**改进点**：
1. 提供一键启动脚本（自动以 `--remote-debugging-port=9222` 启动 Chrome）
2. 后端自动检测 CDP 可用性，前端给出明确引导
3. CDP 连接失败时给出清晰的错误提示和修复步骤

| 维度 | 评价 |
|------|------|
| httpOnly Cookie | ✅ 可读取 |
| 用户体验 | ⭐⭐ 需特殊方式启动 Chrome |
| 安全性 | ⭐⭐ 调试端口暴露有风险 |
| 部署复杂度 | ⭐⭐⭐⭐ 现有代码已实现 |
| 云部署兼容 | ❌ 依赖本地 Chrome |
| 反检测风险 | ✅ 无自动化特征 |
| Cookie 刷新 | ❌ 需手动触发 |

**局限**：
- 必须以调试模式启动 Chrome，普通用户容易遗忘
- 调试端口有安全风险（任何网页都可连接）
- 云部署场景不可用

---

### 方案 C：反向代理

**原理**：在后端设置反向代理，将 `xiaohongshu.com` 代理到同源路径下（如 `/proxy/xhs/`），用户通过代理访问小红书，Cookie 自然落在代理域名下。

| 维度 | 评价 |
|------|------|
| httpOnly Cookie | ⚠️ Cookie domain 被改写，可能不完整 |
| 用户体验 | ⭐⭐⭐ 无需安装，但需通过代理访问 |
| 安全性 | ⭐ 中间人风险，Cookie 经过代理服务器 |
| 部署复杂度 | ⭐ 需处理 JS/CSS/图片等资源代理 |
| 云部署兼容 | ⚠️ 代理流量大，可能被 XHS 封禁 |
| 反检测风险 | ❌ 小红书可检测代理访问 |
| Cookie 刷新 | ❌ 需用户主动通过代理访问 |

**局限**：
- 小红书页面 JS 资源极多，完整代理难度大
- XHS 前端 JS 会检测 origin/referer，代理后可能异常
- 安全风险高（代理可窃取用户凭证）

---

### 方案 D：Bookmarklet / 控制台脚本

**原理**：用户在小红书页面执行一段 JS 脚本，脚本读取 `document.cookie` 并发送到后端。

| 维度 | 评价 |
|------|------|
| httpOnly Cookie | ❌ 无法读取 web_session |
| 用户体验 | ⭐⭐ 需手动操作，技术门槛高 |
| 安全性 | ⭐⭐ 用户需信任脚本 |
| 部署复杂度 | ⭐⭐⭐⭐⭐ 几乎无需开发 |
| 云部署兼容 | ✅ |
| 反检测风险 | ✅ |
| Cookie 刷新 | ❌ 每次需手动执行 |

**局限**：
- **致命缺陷**：无法获取 `httpOnly` 的 `web_session` Cookie
- 仅能获取 `a1`、`webId` 等非 httpOnly Cookie，不足以维持会话

---

### 方案 E：前端 iframe 嵌入

**原理**：在前端页面中嵌入小红书登录页 iframe，用户在 iframe 中扫码登录。

| 维度 | 评价 |
|------|------|
| httpOnly Cookie | ❌ 无法跨域读取 |
| 用户体验 | ⭐⭐⭐ 看似无缝 |
| 安全性 | ⭐ XHS 可通过 X-Frame-Options 阻止 |
| 部署复杂度 | ⭐⭐⭐ |
| 云部署兼容 | ✅ |
| 反检测风险 | ❌ XHS 可能阻止 iframe 嵌入 |

**局限**：
- **致命缺陷**：小红书设置 `X-Frame-Options: DENY`，禁止 iframe 嵌入
- 即使能嵌入，同源策略也阻止读取 Cookie

---

## 方案综合评分

| 方案 | httpOnly | 用户体验 | 安全性 | 部署难度 | 云兼容 | 总分 |
|------|---------|---------|--------|---------|--------|------|
| **A: Chrome 扩展** | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | **⭐⭐⭐⭐⭐** |
| B: CDP 增强 | ✅ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ |
| C: 反向代理 | ⚠️ | ⭐⭐⭐ | ⭐ | ⭐ | ⚠️ | ⭐⭐ |
| D: Bookmarklet | ❌ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐ |
| E: iframe | ❌ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ✅ | ⭐ |

---

## 推荐方案：A（Chrome 扩展）

### 推荐理由

1. **唯一能同时满足所有需求的方案**：可读取 httpOnly Cookie、用户体验好、安全、云部署兼容
2. **自动续期能力**：通过 `chrome.cookies.onChanged` 监听，Cookie 变化时自动同步到后端
3. **引导登录能力**：扩展可打开 XHS 登录页，检测登录完成，自动提取 Cookie
4. **无反检测风险**：不使用任何自动化工具，完全模拟正常用户行为
5. **开发量可控**：Chrome Extension 核心代码约 200-300 行

### 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│                      Chrome Browser                          │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Intent Money     │    │ Chrome Extension               │ │
│  │ Frontend         │    │ (background.js + popup.html)   │ │
│  │                  │    │                                 │ │
│  │  window.         │◄──►│  chrome.cookies.getAll()       │ │
│  │  postMessage     │    │  chrome.cookies.onChanged      │ │
│  │                  │    │  chrome.tabs.onUpdated          │ │
│  └────────┬─────────┘    └──────────────┬──────────────────┘ │
│           │                             │                    │
└───────────┼─────────────────────────────┼────────────────────┘
            │                             │
            ▼                             ▼
     ┌──────────────────────────────────────┐
     │        Intent Money Backend          │
     │  POST /accounts/{platform}/cookie    │
     │  POST /accounts/{platform}/extension │
     │  CookieVault → SQLite               │
     └──────────────────────────────────────┘
```

### 扩展功能清单

1. **Cookie 读取**：一键获取小红书所有 Cookie（含 httpOnly）
2. **登录引导**：打开小红书登录页，检测登录完成
3. **Cookie 监听**：后台监听 Cookie 变化，自动同步
4. **状态展示**：popup 显示当前 Cookie 状态（有效/过期/未登录）
5. **多平台支持**：预留抖音等平台的扩展能力

### 前端改造

1. **检测扩展**：页面加载时检测扩展是否安装，显示不同 UI
2. **扩展通信**：通过 `window.postMessage` 与扩展交互
3. **降级方案**：扩展未安装时，回退到现有 CDP/Playwright 方案

### 后端改造

1. **新增 API**：`POST /accounts/{platform}/extension` 接收扩展发送的 Cookie
2. **Cookie 格式适配**：将 `chrome.cookies.getAll()` 返回的格式转换为 `storage_state` 格式
3. **安全校验**：验证 Cookie 来源，防止伪造

---

## ADDED Requirements

### Requirement: Chrome Extension Cookie 获取
系统 SHALL 通过 Chrome Extension 获取小红书 Cookie，包括 httpOnly 的 `web_session`。

#### Scenario: 用户已登录小红书，一键获取 Cookie
- **WHEN** 用户点击扩展 popup 中的"获取 Cookie"按钮
- **THEN** 扩展调用 `chrome.cookies.getAll({domain: ".xiaohongshu.com"})` 获取所有 Cookie
- **AND** 将 Cookie 通过 HTTP POST 发送到后端 `/accounts/xhs/extension`
- **AND** 后端验证 Cookie 有效性，加密存储，返回成功

#### Scenario: 用户未登录小红书，引导登录
- **WHEN** 用户点击前端页面的"扫码登录"按钮，且扩展已安装
- **THEN** 前端通过 `window.postMessage` 通知扩展
- **AND** 扩展打开新标签页访问 `https://www.xiaohongshu.com`
- **AND** 用户在小红书页面完成扫码登录
- **AND** 扩展通过 `chrome.cookies.onChanged` 检测到 `web_session` 变化
- **AND** 扩展自动提取 Cookie 并发送到后端
- **AND** 前端通过 `window.postMessage` 收到登录成功通知

### Requirement: 扩展安装检测
前端 SHALL 检测 Chrome Extension 是否已安装，并展示相应 UI。

#### Scenario: 扩展已安装
- **WHEN** 用户打开账号管理页面
- **THEN** 前端检测到扩展已安装，显示"扩展已连接"状态
- **AND** "扫码登录"按钮改为"一键登录"（由扩展处理）

#### Scenario: 扩展未安装
- **WHEN** 用户打开账号管理页面
- **THEN** 前端未检测到扩展，显示"安装扩展"引导
- **AND** 保留现有 CDP/Playwright 扫码登录作为降级方案

### Requirement: Cookie 自动续期
系统 SHALL 在 Cookie 变化时自动同步到后端。

#### Scenario: 用户在浏览器中重新登录小红书
- **WHEN** 扩展检测到 `xiaohongshu.com` 的 `web_session` Cookie 发生变化
- **THEN** 扩展自动将新 Cookie 发送到后端
- **AND** 后端更新加密存储的 Cookie

## MODIFIED Requirements

### Requirement: 扫码登录流程
现有扫码登录流程 SHALL 支持扩展模式作为首选方案，CDP/Playwright 作为降级。

登录优先级：Chrome Extension → CDP → Playwright

## REMOVED Requirements

（无移除需求，现有方案作为降级保留）
