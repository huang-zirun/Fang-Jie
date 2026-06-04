# 浏览器扩展检测与状态同步根因修复

## 问题现象

- 安装浏览器扩展后，前端仍然显示"未检测到浏览器扩展"
- 扩展 popup 显示平台"已登录"，但前端账号状态未同步更新
- 用户只能通过扫码登录，无法使用扩展的一键登录和 Cookie 获取功能

## 根因分析

### 根因 1：content script 的 `event.source !== window` 在隔离世界中失效

Chrome MV3 content script 运行在隔离世界，`window` 是页面 `window` 的代理对象。Chrome 官方文档明确指出：

> "The proxy forwards property accesses and method calls to the page's `window`, but strict equality comparisons (`===`) may not work as expected."

当 Vue 前端调用 `window.postMessage({ type: 'INTENT_MONEY_PING' }, '*')` 时，content script 中的 `event.source !== window` 返回 `true`，**所有页面消息被静默丢弃**。前端永远收不到 PONG，2 秒超时后判定扩展未安装。

**位置**：`extension/content.js` L4

### 根因 2：前端扩展检测机制为一次性、无重试

`checkExtension()` 只在 `onMounted` 时执行一次，超时 2 秒。content script 加载可能晚于 Vue 组件挂载，检测失败后永不重试。

**位置**：`frontend/src/views/AccountManage.vue` L200-218

### 根因 3：配置未同步导致 Cookie 自动同步链路断裂

由于检测失败，`configureExtension()` 从未执行，`authToken` 永远为空。`background.js` 的 `chrome.cookies.onChanged` 监听器检测到登录后，因缺少 `authToken` 直接 `return`，跳过同步。

这是一个**级联故障**：content script 消息过滤 bug → 配置无法同步 → cookie 自动同步失效 → 前端和扩展状态完全脱节。

**位置**：`extension/background.js` L24-29

### 根因 4：扩展登录状态未广播到前端

扩展 popup 能检测浏览器中的 cookie 状态，但检测结果不向前端页面广播。前端只能通过后端 API 获取账号绑定状态，无法感知浏览器中实际的登录情况。

## 修复方案

### 1. 修复 content script 消息过滤

移除 `if (event.source !== window) return;`，仅保留 `event.data.source === "intent-money-extension"` 防止消息循环。

### 2. 实现扩展状态广播通道

- background.js 新增 `broadcastStatusToTabs()`，通过 `chrome.tabs.sendMessage` 向所有匹配标签页广播 `STATUS_UPDATE`
- `chrome.cookies.onChanged` 监听器在同步到后端后，同时广播状态到前端
- content.js 新增 `chrome.runtime.onMessage` 监听器，接收 background 广播并转发为 `INTENT_MONEY_STATUS_UPDATE` 给页面

### 3. 重构前端扩展检测机制

- `checkExtension()` 改为指数退避重试：最多 5 次，间隔 1s/2s/3s/4s/5s
- 添加 `visibilitychange` 监听，页面重新可见时触发重检
- 检测成功后立即调用 `configureExtension()` 同步 `authToken` 和 `serverUrl`

### 4. 前端扩展状态同步与 UI 展示

- 新增 `extensionStatus` 响应式对象，存储扩展检测到的各平台状态
- 全局 message 监听接收 `INTENT_MONEY_STATUS_UPDATE`
- 账号卡片显示"浏览器已登录"绿色标识
- 扩展已登录但后端未绑定时，显示"同步到后端"按钮

### 5. 修复 syncCookiesToBackend

`authToken` 缺失时不再直接 `return`，而是记录 warn 并继续尝试同步（`Authorization` header 仅在 `authToken` 存在时附加）。

## 修改文件

| 文件 | 变更 |
|------|------|
| `extension/content.js` | 移除 `event.source !== window`；新增 background → page 状态广播转发 |
| `extension/background.js` | 新增 `broadcastStatusToTabs()`；cookie 变化时广播状态；`syncCookiesToBackend` 不再因 authToken 缺失跳过 |
| `frontend/src/views/AccountManage.vue` | 重写 `checkExtension()` 为重试机制；新增 `extensionStatus` 和状态监听；UI 显示扩展登录状态 |

## 验证

- `vue-tsc -b` 类型检查通过
- `vite build` 生产构建成功

## 经验教训

- Chrome MV3 隔离世界中，`window` 代理对象的严格相等比较不可靠，content script 中不应使用 `event.source === window` 过滤消息
- 扩展检测不能依赖一次性超时，必须设计重试机制
- 扩展架构中，前端检测、配置同步、cookie 同步是级联链路，任何一个节点断裂都会导致整个功能失效
- 扩展状态应主动广播到前端，而非依赖前端轮询或后端状态
