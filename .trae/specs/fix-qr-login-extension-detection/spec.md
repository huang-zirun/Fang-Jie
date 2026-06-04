# 扫码登录后扩展检测与登录状态显示修复 Spec

## Why

用户安装浏览器扩展后，通过 CDP 路径扫码登录成功（后端 confirmed、数据库已保存 Cookie），但前端页面仍显示"未检测到浏览器扩展"，且浏览器扩展弹窗中的登录状态无法正确反映实际登录状态。这是一个架构级问题：CDP/Playwright 扫码登录的 Cookie 仅存在于隔离的浏览器上下文中，从未注入用户真实浏览器，导致扩展无法通过 `chrome.cookies.getAll()` 检测到登录状态。

## What Changes

- **BREAKING** 重构扫码登录成功后的 Cookie 传播机制：QR 登录确认后，通过浏览器扩展将 Cookie 注入用户真实浏览器
- **BREAKING** 扩展 `CHECK_LOGIN` 增加后端 API 降级查询：当本地 Cookie 检测为"未登录"时，查询后端账号绑定状态作为补充判断
- 修复 `manifest.json` 的 `content_scripts.matches` 范围过窄问题，支持更多开发/部署环境
- 前端扫码登录成功后的状态展示逻辑解耦：不再依赖扩展检测结果来决定 UI 状态
- 扩展 popup 增加来源标注：区分"本地 Cookie 检测"和"后端状态同步"两种登录状态来源

## Impact

- Affected specs: 浏览器扩展通信、扫码登录全链路、账号状态展示
- Affected code:
  - `intent-money/extension/manifest.json` — content_scripts 匹配范围
  - `intent-money/extension/background.js` — CHECK_LOGIN 增加后端降级、新增 SET_COOKIES action
  - `intent-money/extension/content.js` — 新增 INTENT_MONEY_SET_COOKIES 消息处理
  - `intent-money/extension/popup/popup.js` — 状态展示增加来源区分
  - `intent-money/extension/popup/popup.html` — UI 增加 Cookie 来源信息
  - `intent-money/frontend/src/views/AccountManage.vue` — 扫码登录成功后的状态更新逻辑
  - `intent-money/backend/app/api/v1/accounts.py` — 新增 Cookie 注入端点
  - `intent-money/backend/app/services/cdp_qrcode_login.py` — 登录确认后触发 Cookie 注入流程

## 根因分析

### 根因 1：CDP/Playwright QR 登录的 Cookie 永远不会到达用户真实浏览器（核心根因）

**数据流断裂点**：

```
用户手机扫码 → CDP控制页/无头浏览器完成登录 → 后端提取storage_state存DB ✅
                                                    ↓
                                            用户真实浏览器的CookieJar ❌ (空!)
                                                    ↓
                                            chrome.cookies.getAll() → 无结果 ❌
                                                    ↓
                                            扩展显示"未登录" / 前端显示"未检测到扩展"
```

**CDP 路径详情**：
- [cdp_qrcode_login.py L128-178](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/cdp_qrcode_login.py#L128-L178)：`start_cdp_qr_login()` 通过 CDP 在用户 Chrome 中创建新标签页，导航到创作者中心登录页
- [cdp_qrcode_login.py L193-209](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/cdp_qrcode_login.py#L193-L209)：登录确认后提取 `storage_state`，**立即关闭 CDP 标签页**
- 关闭后 Cookie 仅存在于数据库中，用户真实浏览器的 CookieJar 中没有这些 Cookie

**Playwright 路径更严重**：
- [qrcode_login.py L73-84](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/qrcode_login.py#L73-L84)：启动的是**完全独立的 headless Chromium 进程**
- 与用户的 Chrome 浏览器完全隔离，Cookie 不可能共享

**对比扩展的工作方式** ([background.js L98-117](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/extension/background.js#L98-L117))：
```javascript
// CHECK_LOGIN: 直接查用户真实浏览器的 CookieJar
const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
const sessionCookie = cookies.find((c) => c.name === cfg.sessionCookie);
return { loggedIn: !!sessionCookie && !sessionCookie.session };
```
这个检查永远无法发现 CDP/Playwright 路径获取的 Cookie。

### 根因 2：content_scripts 匹配范围过窄

[manifest.json L22-27](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/extension/manifest.json#L22-L27)：
```json
"content_scripts": [{
    "matches": ["http://localhost:*/*", "http://127.0.0.1:*/*"],
    "js": ["content.js"]
}]
```

仅匹配 `localhost` 和 `127.0.0.1`。以下场景均会导致 content script 不注入：
- Docker 容器内访问（如 `http://172.17.0.1:xxxx`）
- 局域网其他设备访问（如 `http://192.168.x.x:xxxx`）
- 生产环境 HTTPS 部署
- Vite dev server 通过 `--host` 暴露非 localhost 地址

content script 不注入 → [content.js](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/extension/content.js) 不加载 → `INTENT_MONEY_PING` 无响应 → [AccountManage.vue L200-218](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/frontend/src/views/AccountManage.vue#L200-L218) 设置 `extensionInstalled = false`

### 根因 3：扩展 CHECK_LOGIN 的域名与 CDP 登录目标不匹配

[background.js L1-12](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/extension/background.js#L1-L12)：
```javascript
PLATFORM_CONFIG = {
    xiaohongshu: {
        domain: ".xiaohongshu.com",       // 检查整个 xiaohongshu.com 域
        loginUrl: "https://www.xiaohongshu.com",  // 主站
        sessionCookie: "web_session"
    },
    douyin: {
        domain: ".douyin.com",
        loginUrl: "https://www.douyin.com",
        sessionCookie: "sessionid"
    }
}
```

但 CDP 登录目标是：
- XHS: `https://creator.xiaohongshu.com/login`（创作者中心）
- 抖音: `https://creator.douyin.com/`（创作者中心）

创作者中心的 Session Cookie 可能与主站不同（如 `a1_token`、`passport_csrf_token` 等），而扩展只检查主站的 `web_session` / `sessionid`。即使 Cookie 被注入了真实浏览器，也可能因为 Cookie 名称不匹配而误判为"未登录"。

### 根因 4：前端扫码登录成功后的状态更新依赖扩展检测

[AccountManage.vue L326-364](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/frontend/src/views/AccountManage.vue#L326-L364) 的 `startQrLogin()` 逻辑：
```typescript
if (extensionInstalled.value) {
    // 路径A: 扩展登录（获取Cookie/引导登录）← 如果扩展误判为已安装但通信失败会卡住
} else {
    // 路径B: QR码弹窗 ← 用户实际走的路径
}
```

[AccountManage.vue L366-386](file:///e:/系统文件夹/Desktop/Channing-Fang-Jie/intent-money/frontend/src/views/AccountManage.vue#L366-L386) 的轮询逻辑在 `confirmed` 后调用 `fetchAccounts()` 刷新列表，这部分是正确的。但问题在于：

1. 页面顶部的扩展提示区域（L8-19）始终基于 `extensionInstalled` 状态显示，与 QR 登录是否成功无关
2. QR 登录成功后没有重新触发 `checkExtension()` 检测
3. 用户看到"未检测到浏览器扩展"提示 + 已绑定的账号，产生困惑

## ADDED Requirements

### Requirement: QR 登录确认后 Cookie 注入真实浏览器

系统 SHALL 在 CDP 或 Playwright 路径扫码登录确认后，将获取到的 Cookie 通过浏览器扩展注入用户真实的浏览器 CookieJar 中。

#### Scenario: CDP 路径登录成功后注入 Cookie
- **WHEN** CDP 轮询检测到登录确认（status=confirmed）
- **AND** 后端已保存 storage_state 到数据库
- **THEN** 系统通过 WebSocket/SSE 或轮询机制通知前端
- **AND** 前端向扩展发送 `INTENT_MONEY_SET_COOKIES` 消息，携带平台和 Cookie 数据
- **AND** 扩展调用 `chrome.cookies.set()` 将每个 Cookie 写入用户真实浏览器
- **AND** 扩展返回写入结果

#### Scenario: Playwright 路径登录成功后注入 Cookie
- **WHEN** Playwright 轮询检测到登录确认
- **THEN** 行为同 CDP 路径

#### Scenario: 扩展未安装时的降级
- **WHEN** QR 登录确认成功
- **AND** 前端检测到扩展未安装
- **THEN** 系统跳过 Cookie 注入步骤
- **AND** 前端正常显示登录成功状态
- **AND** 提示用户"可安装扩展以同步 Cookie 到浏览器"

### Requirement: 扩展 CHECK_LOGIN 增加后端 API 降级

系统 SHALL 在扩展的登录状态检测中，当本地 Cookie 检测为"未登录"时，额外查询后端 API 获取账号绑定状态作为补充判断。

#### Scenario: 本地无 Cookie 但后端有绑定记录
- **WHEN** 扩展执行 CHECK_LOGIN
- **AND** `chrome.cookies.getAll()` 未找到有效 session cookie
- **THEN** 扩展向后端发送请求查询 `{platform}` 的绑定状态
- **AND** 若后端返回 `bind_status=bound` 且 `cookie_status=active`，则显示"已登录（来自服务端同步）"
- **AND** 用不同的视觉样式（如虚线圆点）区分于本地 Cookie 检测的"已登录"

#### Scenario: 本地和后端都无记录
- **WHEN** 本地 Cookie 检测为未登录
- **AND** 后端也无绑定记录或 Cookie 已过期
- **THEN** 显示"未登录"

### Requirement: content_scripts 匹配范围扩展

系统 SHALL 扩展 `manifest.json` 中 `content_scripts` 的 `matches` 配置，覆盖常见的开发和部署环境。

#### Scenario: Docker/局域网开发环境
- **WHEN** 用户通过 `http://<docker-ip>:<port>` 或 `http://<lan-ip>:<port>` 访问前端
- **THEN** content script 正常注入
- **AND** PING/PONG 心跳正常工作

#### Scenario: 生产环境部署
- **WHEN** 用户通过 `https://<domain>` 访问前端
- **THEN** content script 正常注入（需要 `<all_urls>` 或具体域名配置）

### Requirement: 前端 QR 登录成功后状态展示解耦

系统 SHALL 确保 QR 登录成功后的 UI 状态正确反映登录结果，不受扩展检测状态影响。

#### Scenario: QR 登录成功但扩展未检测到
- **WHEN** QR 码扫描确认成功（status=confirmed）
- **AND** `fetchAccounts()` 返回该平台账号 `bind_status=bound`
- **THEN** 账号卡片显示正确的状态（正常/待验证等）
- **AND** 顶部扩展提示区独立显示其自身状态（不影响账号卡片）
- **AND** QR 弹窗显示"登录成功"后自动关闭

### Requirement: 扩展增加 SET_COOKIES message handler

系统 SHALL 在 background.js 中新增 `SET_COOKIES` action handler，接收前端发来的 Cookie 列表并使用 `chrome.cookies.set()` 写入用户浏览器。

#### Scenario: 收到 SET_COOKIES 消息
- **WHEN** background.js 收到 `{ action: "SET_COOKIES", platform: "...", cookies: [...] }`
- **THEN** 遍历 cookies 数组，对每个 cookie 调用 `chrome.cookies.set()`
- **AND** 使用正确的 url/domain/path 等参数
- **AND** 返回 `{ success: true, setCount: n, failCount: m }`

## MODIFIED Requirements

### Requirement: manifest.json content_scripts 配置

修改 `matches` 为：
```json
"matches": ["<all_urls>"]
```
或至少包含开发环境和生产环境的常见 URL pattern。

### Requirement: background.js PLATFORM_CONFIG

增加创作者中心相关的 Cookie 检测配置：
```javascript
PLATFORM_CONFIG = {
    xiaohongshu: {
        domain: ".xiaohongshu.com",
        loginUrl: "https://creator.xiaohongshu.com/login",
        sessionCookie: "web_session",
        altCookies: ["a1_token", "web_id"]  // 备选 Cookie 名称
    },
    douyin: {
        domain: ".douyin.com",
        loginUrl: "https://creator.douyin.com/",
        sessionCookie: "sessionid",
        altCookies: ["passport_csrf_token", "ttwid"]  // 备选 Cookie 名称
    }
}
```

### Requirement: AccountManage.vue startQrLogin 和轮询逻辑

修改 `startQrLogin()` 使 QR 登录路径不依赖 `extensionInstalled` 状态来判断入口。
修改轮询 `confirmed` 分支，在 `fetchAccounts()` 之后增加扩展 Cookie 同步调用。

## REMOVED Requirements

（无移除的需求）
