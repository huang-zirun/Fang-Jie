# Tasks

- [x] Task 1: 扩展 manifest.json 更新 — 添加小红书页面 content script 注入
  - [x] SubTask 1.1: 在 `content_scripts` 中添加 `"*://*.xiaohongshu.com/*"` 匹配规则，注入 `xhs_content.js`
  - [x] SubTask 1.2: 确认 `host_permissions` 已包含 `"*://*.xiaohongshu.com/*"`（当前已有）
  - [x] SubTask 1.3: 确认 `permissions` 已包含 `"scripting"`（当前已有，用于动态注入 Main World 脚本）

- [x] Task 2: 创建小红书 Main World 脚本（`xhs_main_world.js`）— 在页面主世界执行的核心逻辑
  - [x] SubTask 2.1: 实现 `window.__INIT_PROPS__` SSR 数据读取和解析
  - [x] SubTask 2.2: 实现 fetch/XHR monkey-patch，拦截 `edith.xiaohongshu.com/api/sns/web/` 的请求和响应
  - [x] SubTask 2.3: 实现 X-s / X-t 签名函数定位和调用逻辑
  - [x] SubTask 2.4: 实现通过 `window.postMessage` 将数据传递给 content script

- [x] Task 3: 创建小红书页面 content script（`xhs_content.js`）— 消息中转和 DOM 解析
  - [x] SubTask 3.1: 实现监听 Main World 脚本的 `postMessage`，转发给 background
  - [x] SubTask 3.2: 实现 DOM 解析回退逻辑，当 SSR 数据不可用时从搜索结果卡片提取数据
  - [x] SubTask 3.3: 实现监听 background 消息，按需触发 Main World 脚本执行
  - [x] SubTask 3.4: 实现页面加载完成时自动提取 SSR 数据并上报

- [x] Task 4: 扩展 background.js 添加小红书抓取消息处理器
  - [x] SubTask 4.1: 添加 `SCRAPE_XHS_SEARCH` 消息处理器，接收关键词参数
  - [x] SubTask 4.2: 实现分层降级逻辑：拦截缓存 → 主动 API 调用 → SSR 提取 → DOM 解析
  - [x] SubTask 4.3: 实现 Service Worker fetch 调用小红书搜索 API（使用 Cookie + 签名）
  - [x] SubTask 4.4: 实现请求拦截数据缓存管理（存储最近拦截的 API 响应）
  - [x] SubTask 4.5: 实现抓取结果通过 HTTPS POST 同步到后端 `/market/extension-scrape-xhs` 端点
  - [x] SubTask 4.6: 添加 `CHECK_XHS_TAB` 和 `OPEN_XHS_SEARCH` 辅助消息处理器

- [x] Task 5: 后端新增小红书扩展抓取数据接收端点
  - [x] SubTask 5.1: 在 `market.py` 中添加 `POST /market/extension-scrape-xhs` 端点
  - [x] SubTask 5.2: 创建请求 schema（`XhsExtensionScrapeData`），包含 keyword、platform_id、notes 列表、source
  - [x] SubTask 5.3: 实现数据验证和 `MarketHot` 记录创建逻辑，`hot_type` 标记为 `"xhs_extension_scraped"` 或 `"xhs_extension_intercepted"`
  - [x] SubTask 5.4: 添加认证（Bearer token，与扩展现有认证方式一致）

- [x] Task 6: 后端市场服务集成小红书扩展抓取
  - [x] SubTask 6.1: 在 `market_service.py` 中添加 `scrape_xhs_via_extension()` 函数
  - [x] SubTask 6.2: 修改定时任务逻辑，小红书平台优先尝试扩展抓取

- [ ] Task 7: 端到端测试与验证
  - [ ] SubTask 7.1: 手动测试扩展在小红书搜索页的 SSR 数据提取
  - [ ] SubTask 7.2: 手动测试请求拦截功能（用户浏览时被动捕获 API 响应）
  - [ ] SubTask 7.3: 手动测试 Service Worker fetch 调用小红书 API（含签名）
  - [ ] SubTask 7.4: 测试抓取数据同步到后端并正确创建 MarketHot 记录
  - [ ] SubTask 7.5: 测试分层降级：API 失败 → SSR → DOM 的自动降级

# Task Dependencies
- [Task 2] depends on [Task 1]（Main World 脚本需要 manifest.json 注册或动态注入）
- [Task 3] depends on [Task 2]（content script 依赖 Main World 脚本的数据输出）
- [Task 4] depends on [Task 3]（background 需要与 content script 通信）
- [Task 5] 独立（后端端点可并行开发）
- [Task 6] depends on [Task 4] and [Task 5]（市场服务需要扩展抓取和后端端点都就绪）
- [Task 7] depends on [Task 6]（端到端测试需要所有组件就绪）
