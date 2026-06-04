# Tasks

- [x] Task 1: 扩展 manifest.json 更新 — 添加抖音页面 content script 注入和 scripting 权限
  - [x] SubTask 1.1: 在 `content_scripts` 中添加 `"*://*.douyin.com/*"` 匹配规则，注入新的抖音专用 content script（`douyin_content.js`）
  - [x] SubTask 1.2: 在 `permissions` 中添加 `"scripting"` 权限
  - [x] SubTask 1.3: 确认 `host_permissions` 已包含 `"*://*.douyin.com/*"`（当前已有）

- [x] Task 2: 创建抖音页面 content script（`douyin_content.js`）— 读取 SSR 数据和 DOM 解析
  - [x] SubTask 2.1: 实现 Main World 注入脚本，读取 `window.__INIT_PROPS__` / `window.__NEXT_DATA__` 中的搜索结果数据
  - [x] SubTask 2.2: 实现 DOM 解析回退逻辑，当 SSR 数据不可用时从搜索结果卡片提取数据
  - [x] SubTask 2.3: 实现 X-Bogus 签名函数调用逻辑（通过 Main World 注入）
  - [x] SubTask 2.4: 监听 background 消息，按需提取数据并通过 `chrome.runtime.sendMessage` 返回

- [x] Task 3: 扩展 background.js 添加抓取消息处理器
  - [x] SubTask 3.1: 添加 `SCRAPE_DOUYIN_SEARCH` 消息处理器，接收关键词参数
  - [x] SubTask 3.2: 实现 Service Worker fetch 调用抖音搜索 API（使用 `chrome.cookies.getAll` 获取 Cookie）
  - [x] SubTask 3.3: 实现 API 调用失败时回退到 content script SSR 数据提取
  - [x] SubTask 3.4: 实现抓取结果通过 HTTPS POST 同步到后端 `/api/v1/market/extension-scrape` 端点

- [x] Task 4: 后端新增扩展抓取数据接收端点
  - [x] SubTask 4.1: 在 `market.py` 中添加 `POST /market/extension-scrape` 端点
  - [x] SubTask 4.2: 创建请求 schema（`ExtensionScrapeData`），包含 keyword、platform_id、videos 列表
  - [x] SubTask 4.3: 实现数据验证和 `MarketHot` 记录创建逻辑，`hot_type` 标记为 `"extension_scraped"`
  - [x] SubTask 4.4: 添加认证（Bearer token，与扩展现有认证方式一致）

- [x] Task 5: 后端定时任务集成扩展抓取触发
  - [x] SubTask 5.1: 在 `market_service.py` 中添加 `scrape_via_extension()` 函数，通过扩展通信触发抓取
  - [x] SubTask 5.2: 修改定时任务逻辑，优先尝试扩展抓取，失败时回退到后端 API 爬虫
  - [x] SubTask 5.3: 实现扩展在线状态检测（通过前端 WebSocket 或后端心跳端点）

- [x] Task 6: 前端集成 — 点击"今日任务"时自动触发扩展抓取
  - [x] SubTask 6.1: 在 `content.js` 中添加 `INTENT_MONEY_TRIGGER_SCRAPE` 消息处理器
  - [x] SubTask 6.2: 在 `PlatformSelect.vue` 中添加扩展在线检测和抓取触发逻辑
  - [x] SubTask 6.3: 选择抖音平台时，扩展在线则等待 5 秒后调用 `createTask`
  - [x] SubTask 6.4: 扩展不在线时直接调用 `createTask`，无额外延迟

- [x] Task 7: 端到端测试与验证
  - [x] SubTask 7.1: 验证 `content.js` 新增消息处理器能正确转发到 background
  - [x] SubTask 7.2: 验证 `PlatformSelect.vue` 扩展检测和延迟逻辑正确
  - [x] SubTask 7.3: 验证后端导入无错误

# Task Dependencies
- [Task 2] depends on [Task 1]（content script 需要 manifest.json 注册）
- [Task 3] depends on [Task 2]（background 需要与 content script 通信）
- [Task 4] 独立（后端端点可并行开发）
- [Task 5] depends on [Task 3] and [Task 4]（定时任务需要扩展抓取和后端端点都就绪）
- [Task 6] depends on [Task 5]（端到端测试需要所有组件就绪）
