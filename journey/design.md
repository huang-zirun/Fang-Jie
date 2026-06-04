# Intent Money OS — 项目设计快照

> 最后更新: 2026-06-03（扩展数据抓取架构）

## 项目定位

意图变现 OS — 帮助内容创作者从"意图"到"变现"的全流程工具。核心链路：爆款选题 → AI 生成脚本 → 视频发布 → 数据追踪 → 诊断优化。

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async) + SQLite (aiosqlite)
- **前端**: Vue 3 + Vant UI + TypeScript
- **AI**: DeepSeek V4 Flash (via OpenRouter)
- **浏览器自动化**: Playwright
- **浏览器扩展**: Chrome Extension MV3 (cookies / tabs / storage / scripting 权限)，支持 Cookie 同步 + 抖音页面数据抓取
- **部署**: Docker Compose (FastAPI + Frontend + Nginx) → `https://trades.zzy88.com`

## 核心架构决策

### 账号绑定双路径架构

系统支持两条账号绑定路径，按优先级自动选择：

1. **浏览器扩展路径** (`extension/`): 用户安装 Chrome Extension，前端页面通过 `postMessage` 与 content script 通信（content script 不得使用 `event.source === window` 过滤），background service worker 通过 `chrome.cookies` API 获取平台 Cookie 并同步到后端，同时通过 `chrome.tabs.sendMessage` 向前端广播登录状态变化。最佳用户体验，支持一键获取和后台自动同步。
2. **Playwright 路径** (`qrcode_login.py`): 未安装扩展时使用，启动 Playwright 无头浏览器完成扫码登录。

**关键约束**：
- 两条路径最终都存储为 Playwright `storage_state` 格式，确保后续数据抓取兼容。
- 扩展路径依赖 `content_scripts` 的 `matches` 包含部署域名，否则前端与扩展通信中断。

### Cookie 存储格式

扫码登录保存的是 Playwright `storage_state` JSON 格式（`{"cookies": [...], "origins": [...]}`），而非传统的 `name=value; name=value` 字符串。手动导入 Cookie 仍使用字符串格式。验证器需要同时支持两种格式。

**Chrome 扩展 API → Playwright storage_state 转换必须注意**：
- `sameSite` 值域不同：Chrome API 用 `"no_restriction"` / `"lax"` / `"strict"` / `"unspecified"`，Playwright 用 `"None"` / `"Lax"` / `"Strict"`。不能简单 `.capitalize()`，必须用映射表转换。
- 过期时间字段名不同：Chrome API 用 `expirationDate`（Unix 时间戳秒），Playwright 用 `expires`。
- 平台名称不统一：扩展内部用 `"xiaohongshu"` / `"douyin"`，后端数据库用 `"xhs"` / `"douyin"`，后端通过 `_normalize_platform()` 做别名映射。
- **Cookie domain 子域隔离**：扩展 `chrome.cookies.getAll({ domain: ".xiaohongshu.com" })` 返回的 Cookie 保留了原始子域名（如 `www.xiaohongshu.com`），但验证器访问的是 `creator.xiaohongshu.com`。Playwright 遵循 RFC 6265，domain 为 `www.xiaohongshu.com` 的 Cookie 不会发送到 `creator.xiaohongshu.com`。后端必须通过 `_normalize_cookie_domain()` 将所有子域名统一规范化为父域名（`.xiaohongshu.com` / `.douyin.com`），确保跨子域可用。

### Cookie 验证统一入口

所有平台的 Cookie 验证通过 `cookie_lifecycle.validate_platform_cookie()` 统一入口分发：
- XHS → `xhs_cookie_validator.validate_xhs_cookie()` (Playwright 浏览器验证)
- 抖音 → `douyin_cookie_validator.validate_douyin_cookie()` (Playwright 浏览器验证)

`accounts.py` 和 `cookie_lifecycle.py` 不再各自实现验证逻辑。

### 扩展 Cookie 同步验证策略（2026-06-03 修复）

**问题**：用户在浏览器中正常登录小红书，使用扩展获取Cookie并同步时，后端验证失败返回400错误，导致Cookie无法保存。验证器使用Playwright headless浏览器验证，可能因反爬虫机制误判有效Cookie为无效。

**解决方案**：采用"先保存后验证"策略
1. `extension_cookie_login` 接收Cookie后，**立即保存**到数据库，状态设为 `"pending"`
2. **快速响应**：立即返回成功响应给前端（不等待验证）
3. **后台异步验证**：使用 `asyncio.create_task` 启动后台验证任务
4. **状态更新**：验证完成后，状态更新为 `"active"` 或 `"expired"`

**验证器改进**：
- 增加超时时间：页面加载30秒，等待5秒
- 增强反检测：添加 `--disable-web-security` 等参数
- 多端点验证：先尝试创作者中心，失败后尝试个人主页
- 详细日志：记录验证过程每个关键步骤

**权衡**：
- 优点：用户体验好，立即得到响应；即使验证失败，Cookie也已保存
- 缺点：前端需要支持 `"pending"` 状态显示；可能短暂显示"待验证"状态

### 扩展数据抓取架构（2026-06-03 新增）

移除 CDP 模块后，后端直接调用抖音内部 API 返回 404，`market_hots` 表为空。利用浏览器扩展的真实浏览器环境，将扩展升级为数据抓取通道。

**抓取流程（三级降级）**：
1. **Service Worker fetch + 真实 Cookie**：扩展 background 使用 `chrome.cookies.getAll` 获取用户 Cookie，fetch 调用抖音搜索 API `/aweme/v1/search/item/`，携带 X-Bogus 签名
2. **SSR 数据提取**：API 失败时，通过 content script 在抖音页面注入 Main World 脚本，读取 `window.__INIT_PROPS__` 中的结构化搜索数据
3. **DOM 解析回退**：SSR 不可用时，从搜索结果卡片提取视频 ID、标题、作者、统计数据

**数据回传**：扩展抓取完成后，直接通过 HTTPS POST 将数据提交到后端 `POST /api/v1/market/extension-scrape`，后端创建 `hot_type="extension_scraped"` 的 MarketHot 记录。

**前端集成**：用户在前端选择抖音平台生成任务时（`PlatformSelect.vue`），先通过 `postMessage` 检测扩展是否在线（1 秒 PING），若在线则触发 `SCRAPE_DOUYIN_SEARCH` 并等待 5 秒，让扩展有时间完成抓取并提交数据，然后再调用 `createTask` API。扩展不在线时无额外延迟，直接生成任务。

**关键约束**：
- Service Worker 30 秒空闲超时：单次抓取需在 30 秒内完成（实际 1-3 秒）
- X-Bogus 签名：通过 Main World 注入调用抖音页面签名函数，失败时回退到 SSR/DOM
- 扩展依赖用户浏览器运行：无法无人值守，但真实浏览器环境反爬检测难度最高
- 仅支持抖音：小红书扩展抓取暂未实现（XHS API 相对稳定，后端爬虫可用）

## 已知约束与权衡

- **SQLite**: 不支持并发写入，使用 `render_as_batch=True` 兼容 Alembic 迁移
- **扩展域名限制**: `content_scripts` 的 `matches` 必须显式包含部署域名（如 `https://trades.zzy88.com/*`），否则前端无法检测扩展
- **扩展消息过滤**: Chrome MV3 content script 运行在隔离世界，`window` 是代理对象，**禁止使用 `event.source === window`** 过滤 `postMessage`，否则页面消息会被静默丢弃。正确做法是通过 `event.data.source === 'intent-money-extension'` 防止消息循环。
- **扩展同步错误处理**: `syncCookiesToBackend` 必须向上抛出异常，不能吞掉错误仅 `console.error`，否则调用方（弹窗、自动同步）无法感知失败，用户看到"同步成功"但后端实际未收到数据。
- **扩展检测可靠性**: content script 加载时机晚于前端 `onMounted`，检测机制必须实现重试（指数退避，最多 5 次）+ `visibilitychange` 重检。
- **平台反爬**: 小红书和抖音都有反自动化检测，需要注入 stealth.js 脚本
- **Cookie 有效期**: 平台 Cookie 会过期，需要定期验证和重新登录
- **Cookie domain 规范化**: 扩展获取的 Cookie 可能来自 `www.xiaohongshu.com` 或 `creator.xiaohongshu.com`，但验证器访问的是 `creator.xiaohongshu.com`。必须将所有 Cookie domain 统一为 `.xiaohongshu.com` / `.douyin.com`，否则 Playwright 不会跨子域发送 Cookie，验证必然失败
- **扩展登录状态判断**: 不能用 `!sessionCookie.session` 判断登录态，因为会话 Cookie（无过期时间）的 `session` 为 `true` 会导致误判为"未登录"。应改用 `!!sessionCookie.value` 判断

## 关键模块

| 模块 | 职责 |
|------|------|
| `extension/` | Chrome Extension MV3：content script 桥接、background Cookie 监听与同步、抖音页面数据抓取 |
| `extension/douyin_content.js` | 抖音页面专用 content script：SSR 数据提取、DOM 解析、X-Bogus 签名辅助 |
| `accounts.py` | 账号管理 REST API（含扩展 Cookie 接收端点 `/extension`） |
| `api/v1/market.py` | 市场数据 API（含扩展数据接收端点 `/extension-scrape`、触发端点 `/trigger-extension-scrape`） |
| `services/market_service.py` | 市场数据分析、扩展抓取协调、定时任务集成 |
| `qrcode_login.py` | Playwright 路径扫码登录 |
| `xhs_cookie_validator.py` | 小红书 Cookie 浏览器验证 |
| `douyin_cookie_validator.py` | 抖音 Cookie 浏览器验证 |
| `cookie_lifecycle.py` | Cookie 生命周期管理 + 统一验证入口 |
| `cookie_vault.py` | Cookie AES-GCM 加密存储 |
