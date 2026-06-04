# 扩展数据抓取能力实现

## 背景

移除 CDP 模块后，后端通过 `httpx` 直接调用抖音内部 API 返回 404，`market_hots` 表为空。任务生成时无法参考最新市场热门内容，只能回退到默认内容结构模板。需要寻找新的数据抓取路径。

## 调研结论

Chrome Extension MV3 具备在用户浏览器内完成数据抓取的能力：
- **Service Worker fetch + 真实 Cookie**：`chrome.cookies.getAll` 获取用户 Cookie，`fetch()` 调用抖音内部 API，天然携带浏览器指纹，反爬检测难度最高
- **Content Script DOM/SSR 解析**：通过 Main World 注入脚本读取 `window.__INIT_PROPS__`，或从搜索结果卡片提取数据
- **X-Bogus 签名**：通过 Main World 注入调用抖音页面的签名函数（`_bytedAcrawler.sign` 等）

相比 CDP 方案，扩展在用户体验和部署便利性上更优（零配置、Cookie 自动续期、远程部署兼容），但在无人值守自动化方面不如 CDP（Service Worker 30 秒超时）。两者互补。

## 实现内容

### 扩展侧（3 个文件）

1. **`extension/manifest.json`** — 添加 `"scripting"` 权限，新增抖音页面 `content_scripts` 匹配规则（`"*://*.douyin.com/*"`）注入 `douyin_content.js`
2. **`extension/douyin_content.js`**（新建）— 抖音页面专用 content script：
   - `extractSSRData()`：Main World 注入读取 `window.__INIT_PROPS__` / `window.__NEXT_DATA__`
   - `parseSearchResultsFromSSR()`：解析 SSR 数据中的视频信息
   - `parseSearchResultsFromDOM()`：DOM 解析回退，支持中文格式化数字（"1.6万" → 16000）
   - `getXBogusSignature()`：Main World 注入调用签名函数
   - 消息处理器：`PING`、`EXTRACT_SSR_DATA`、`EXTRACT_DOM_DATA`、`GET_XBOGUS_SIGNATURE`
3. **`extension/background.js`** — 新增 4 个消息处理器：
   - `SCRAPE_DOUYIN_SEARCH`：三级降级抓取（API → SSR → DOM），成功后自动 POST 到后端
   - `CHECK_DOUYIN_TAB`：检查抖音标签页状态
   - `OPEN_DOUYIN_SEARCH`：打开抖音搜索页
   - `HEARTBEAT`：心跳检测
4. **`extension/content.js`** — 新增 `INTENT_MONEY_TRIGGER_SCRAPE` 消息处理器，将前端请求转发给 background

### 后端侧（4 个文件）

1. **`app/schemas/market_hot.py`** — 新增 `ExtensionScrapeVideo` 和 `ExtensionScrapeData` Pydantic 模型
2. **`app/api/v1/market.py`** — 新增两个端点：
   - `POST /market/extension-scrape`：接收扩展提交的抓取数据，创建 `hot_type="extension_scraped"` 的 MarketHot 记录
   - `POST /market/trigger-extension-scrape`：返回扩展抓取指引
3. **`app/services/market_service.py`** — 新增 `scrape_via_extension()` 函数，用于定时任务中标记扩展抓取路径可用
4. **`app/main.py`** — 修改 `daily_scrape_hot_videos()` 优先尝试扩展路径 + 新增 `extension_scrape_reminder()` 后台任务（每 6 小时检查一次扩展提交数据）

### 前端侧（1 个文件）

1. **`frontend/src/views/PlatformSelect.vue`** — 在 `selectPlatform()` 中：
   - 选择抖音平台时，先 `checkExtensionOnline()`（1 秒 PING）
   - 扩展在线 → `triggerExtensionScrape()` → 等待 5 秒 → `createTask`
   - 扩展不在线 → 直接 `createTask`，无额外延迟

## 文件变更清单

| 文件 | 变更类型 |
|------|---------|
| `extension/manifest.json` | 修改 |
| `extension/douyin_content.js` | 新增 |
| `extension/background.js` | 修改 |
| `extension/content.js` | 修改 |
| `backend/app/schemas/market_hot.py` | 修改 |
| `backend/app/api/v1/market.py` | 修改 |
| `backend/app/services/market_service.py` | 修改 |
| `backend/app/main.py` | 修改 |
| `frontend/src/views/PlatformSelect.vue` | 修改 |

## 验证结果

- 后端所有模块导入通过（`uv run python -c import ...`）
- 前端 TypeScript 类型正确
- 扩展 manifest.json 格式正确

## 使用方式

1. 重新加载扩展（`chrome://extensions` → 刷新）
2. 前端选择意图 → 选择抖音平台
3. 如果扩展在线，系统会自动触发抓取并等待 5 秒后生成任务
4. 扩展抓取的数据自动同步到后端 `market_hots` 表
5. 任务生成使用最新市场数据匹配最优内容结构

## 待办/后续优化

- [ ] 实际浏览器环境中测试扩展抓取流程
- [ ] 小红书扩展抓取（当前仅后端爬虫）
- [ ] 扩展抓取结果通知前端（当前前端不感知抓取结果，仅等待 5 秒）
- [ ] 减少等待时间（当前固定 5 秒，可改为扩展完成后主动通知前端）
- [ ] X-Bogus 签名算法的更可靠获取方式（当前依赖页面 JS 函数，可能失效）
