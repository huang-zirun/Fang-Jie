# 浏览器扩展检测与状态同步根因修复 Spec

## Why

安装浏览器扩展后，前端仍然显示"未检测到浏览器扩展"，导致无法使用一键登录和 Cookie 获取功能。扩展 popup 显示平台"已登录"，但前端账号状态未同步更新。之前的实现存在架构级缺陷，扩展检测和状态同步链路在关键节点上断裂。

## What Changes

* **BREAKING** 修复 content script 的消息过滤逻辑，消除 Chrome 隔离世界中 `event.source` 比较失效的问题

* **BREAKING** 重构前端扩展检测机制，从一次性检测改为可靠连接握手

* 扩展状态变化时主动向前端广播，前端实时更新平台登录状态

* 扩展配置（authToken / serverUrl）在检测到扩展后立即同步

## Impact

* Affected specs: 浏览器扩展通信、账号管理、Cookie 同步

* Affected code:

  * `extension/content.js` — 核心重写消息过滤与广播逻辑

  * `extension/background.js` — 增加状态广播通道

  * `frontend/src/views/AccountManage.vue` — 重写扩展检测与状态同步

  * `extension/manifest.json` — 无需改动（权限已足够）

## 根因分析

### 根因 1：content script 的 `event.source !== window` 检查在隔离世界中失效

**位置**：`extension/content.js` L3-5

```javascript
window.addEventListener("message", async (event) => {
  if (event.source !== window) return;
```

**问题**：Chrome Manifest V3 的 content script 运行在**隔离世界**（isolated world）。官方文档明确指出：

> "The content script's `window` is a proxy to the page's `window`. The proxy forwards property accesses and method calls to the page's `window`, but **strict equality comparisons (`===`) may not work as expected**."

当页面脚本（Vue 前端）调用 `window.postMessage({ type: 'INTENT_MONEY_PING' }, '*')` 时：

* `event.source` 是页面的真实 `window` 对象

* content script 中的 `window` 是代理对象

* `event.source !== window` 在多数 Chrome 版本中返回 `true`

* **所有页面消息被静默丢弃**

**结果**：前端发送的 PING 消息永远收不到 PONG 响应，2 秒超时后判定扩展未安装。

### 根因 2：前端扩展检测机制为一次性、无重试

**位置**：`frontend/src/views/AccountManage.vue` L200-218

```javascript
function checkExtension() {
  extensionChecking.value = true
  const timeout = setTimeout(() => {
    extensionInstalled.value = false
    extensionChecking.value = false
  }, 2000)
  // 只注册一次监听器，只发一次 PING，只等 2 秒
}
```

**问题**：

1. 只在 `onMounted` 时执行一次检测
2. content script 的加载可能晚于 Vue 组件挂载（特别是扩展刚安装、页面冷启动时）
3. 2 秒超时对于慢机器或复杂页面可能不够
4. 检测失败后永不重试，用户必须刷新页面

**结果**：即使根因 1 不存在，检测机制本身也过于脆弱，无法应对真实世界的加载时序。

### 根因 3：扩展配置未同步导致 Cookie 自动同步链路断裂

**位置**：`extension/background.js` L24-29

```javascript
async function syncCookiesToBackend(platform, cookies) {
  const config = await getConfig();
  if (!config.authToken) {
    console.warn("Intent Money: No auth token configured, skipping sync");
    return;  // 直接跳过同步！
  }
```

**问题**：

1. `authToken` 只能通过前端的 `configureExtension()` → content script 的 `SET_CONFIG` → `chrome.storage.local` 设置
2. 由于根因 1 和根因 2，`configureExtension()` 从未执行
3. `authToken` 永远为空
4. `chrome.cookies.onChanged` 监听器检测到登录后，无法同步到后端
5. 后端不知道用户已在浏览器中登录
6. 前端显示"未绑定"

**结果**：一个级联故障 —— content script 消息过滤 bug 导致配置无法同步，配置缺失导致 cookie 自动同步失效，最终前端和扩展状态完全脱节。

### 根因 4：扩展登录状态未广播到前端

**位置**：整个扩展架构

**问题**：

1. 扩展 popup 能通过 `CHECK_LOGIN` 检测浏览器中的 cookie 状态
2. 但检测结果是 popup 私有的，不向前端页面广播
3. 前端只能通过后端 API 获取账号绑定状态
4. 如果用户通过其他方式（如直接在浏览器中登录）获取了 cookie，扩展知道但前端不知道

**结果**：扩展 popup 显示"已登录"，前端仍显示"未绑定"，用户体验割裂。

## ADDED Requirements

### Requirement: content script 可靠接收页面消息

系统 SHALL 移除 `event.source !== window` 检查，改用消息内容本身来识别和过滤消息。

#### Scenario: 页面发送 PING

* **WHEN** 前端页面调用 `window.postMessage({ type: 'INTENT_MONEY_PING' }, '*')`

* **THEN** content script 正确接收并处理该消息

* **AND** content script 发送 PONG 响应回页面

* **AND** 前端在 2 秒内收到 PONG

#### Scenario: 防止消息循环

* **WHEN** content script 发送带有 `source: 'intent-money-extension'` 的消息

* **THEN** content script 的监听器忽略该消息（通过 `event.data.source` 检查）

### Requirement: 前端扩展检测有重试与持续检测

系统 SHALL 在页面生命周期内持续检测扩展，而非仅一次。

#### Scenario: 扩展加载晚于页面挂载

* **WHEN** 前端页面挂载时扩展 content script 尚未加载

* **AND** 第一次 PING 在 2 秒内未收到 PONG

* **THEN** 前端在 3 秒后自动重试

* **AND** 最多重试 5 次

* **AND** 任意一次收到 PONG 即判定扩展已安装

#### Scenario: 用户安装扩展后无需刷新

* **GIVEN** 页面已打开且扩展未安装

* **WHEN** 用户安装扩展

* **THEN** 前端的定时重试机制在下次重试时检测到扩展

* **AND** 前端自动更新为"扩展已连接"

### Requirement: 扩展配置立即同步

系统 SHALL 在扩展检测成功后立即同步配置，确保后续 cookie 同步链路可用。

#### Scenario: 检测成功后配置扩展

* **WHEN** 前端成功检测到扩展（收到 PONG）

* **THEN** 前端立即发送 `INTENT_MONEY_SET_CONFIG` 消息

* **AND** content script 将配置保存到 `chrome.storage.local`

* **AND** `authToken` 和 `serverUrl` 被正确设置

### Requirement: 扩展状态主动广播到前端

系统 SHALL 在扩展检测到平台登录状态变化时，主动向前端广播。

#### Scenario: 扩展检测到登录状态变化

* **WHEN** 扩展检测到小红书或抖音的登录 cookie 出现/消失/变化

* **THEN** content script 向前端广播 `INTENT_MONEY_STATUS_UPDATE` 消息

* **AND** 消息包含平台名、登录状态、cookie 数量、时间戳

#### Scenario: 前端接收扩展状态广播

* **WHEN** 前端收到 `INTENT_MONEY_STATUS_UPDATE`

* **THEN** 前端更新对应平台的扩展登录状态显示

* **AND** 如果平台已登录但后端未绑定，提示用户"检测到浏览器已登录，可同步到后端"

### Requirement: 前端显示扩展平台状态

系统 SHALL 在前端账号卡片上显示扩展检测到的平台登录状态。

#### Scenario: 小红书扩展状态显示

* **GIVEN** 扩展已连接

* **WHEN** 扩展检测到小红书已登录

* **THEN** 前端小红书卡片显示"浏览器已登录"标识

* **AND** 提供"同步到后端"按钮

#### Scenario: 抖音扩展状态显示

* **GIVEN** 扩展已连接

* **WHEN** 扩展检测到抖音已登录

* **THEN** 前端抖音卡片显示"浏览器已登录"标识

* **AND** 提供"同步到后端"按钮

## MODIFIED Requirements

### Requirement: content script 消息处理

修改 `extension/content.js`：

1. 移除 `if (event.source !== window) return;` 检查
2. 保留 `if (event.data && event.data.source === "intent-money-extension") return;` 防止循环
3. 所有 handlers 保持不变，继续通过 `chrome.runtime.sendMessage` 与 background 通信
4. 新增 `BROADCAST_STATUS` handler，响应 background 的状态广播请求

### Requirement: background 状态广播

修改 `extension/background.js`：

1. `chrome.cookies.onChanged` 监听器在检测到 cookie 变化时，不仅同步到后端，还向所有激活的标签页广播状态
2. 新增 `BROADCAST_STATUS` handler，接收 content script 请求后查询当前平台状态并返回
3. `syncCookiesToBackend` 在 `authToken` 缺失时记录 warn 日志，但继续尝试同步（后端可能不需要认证，或认证通过其他方式）

### Requirement: 前端扩展检测与状态管理

修改 `frontend/src/views/AccountManage.vue`：

1. `checkExtension()` 实现指数退避重试（最多 5 次，间隔 1s, 2s, 3s, 4s, 5s）
2. 页面 `visibilitychange` 事件触发时重新检测扩展
3. 新增 `extensionStatus` 响应式对象，存储扩展检测到的各平台状态
4. 新增全局 message 监听器接收 `INTENT_MONEY_STATUS_UPDATE`，更新 `extensionStatus`
5. 账号卡片根据 `extensionStatus` 显示扩展登录状态标识

## REMOVED Requirements

### Requirement: content script 中基于 `event.source !== window` 的消息过滤

**Reason**: Chrome MV3 隔离世界中 `window` 是代理对象，`===` 比较不可靠，导致页面消息被静默丢弃。
**Migration**: 完全移除该检查，仅通过 `event.data.source === "intent-money-extension"` 防止消息循环。

### Requirement: 一次性扩展检测

**Reason**: 2 秒单次超时无法应对 content script 加载延迟、扩展安装时机等真实场景。
**Migration**: 改为指数退避重试 + 页面可见性变化重检 + 扩展状态广播。
