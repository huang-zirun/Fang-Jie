# 小红书扩展实时数据抓取 Spec

## Why
后端 `XhsScraper` 通过 httpx 直接调用小红书 API 时缺少 X-s / X-t 签名头，导致请求被拒绝或返回空数据，市场热门数据无法获取。浏览器扩展已具备小红书 Cookie 获取能力且拥有 `*.xiaohongshu.com` 的 `host_permissions`，可以扩展为在用户浏览器内完成数据抓取，利用真实浏览器环境绕过签名校验和反爬限制。

## What Changes
- **新增** 扩展小红书页面 content script 注入（`manifest.json` 添加 `content_scripts` 匹配 `*://*.xiaohongshu.com/*`）
- **新增** `xhs_content.js`：小红书页面 SSR 数据提取、DOM 解析、X-s/X-t 签名获取、请求拦截
- **新增** `xhs_main_world.js`：Main World 脚本，用于读取 `window.__INIT_PROPS__`、调用 XHS 签名函数、monkey-patch fetch/XHR 拦截 API 响应
- **新增** 扩展 background.js 中小红书搜索 API 调用逻辑（`SCRAPE_XHS_SEARCH` 消息处理器）
- **新增** 扩展请求拦截逻辑：被动捕获用户浏览时产生的 XHS API 响应数据
- **新增** 后端 API 端点接收扩展提交的小红书市场数据（`POST /market/extension-scrape-xhs`）
- **修改** `manifest.json`：添加小红书页面 content script 匹配规则
- **修改** `background.js`：添加小红书搜索抓取消息处理器和请求拦截数据缓存
- **修改** `market_service.py`：支持从扩展提交的小红书数据创建 MarketHot 记录

## Impact
- Affected specs: 市场数据抓取架构（扩展抓取从仅支持抖音 → 同时支持抖音和小红书）
- Affected code: `extension/manifest.json`、`extension/background.js`、`extension/xhs_content.js`（新增）、`extension/xhs_main_world.js`（新增）、`backend/app/api/v1/market.py`、`backend/app/services/market_service.py`

## ADDED Requirements

### Requirement: 小红书页面 Content Script 注入
扩展 SHALL 在小红书页面注入 content script，具备读取页面 DOM、SSR 数据和拦截 API 响应的能力。

#### Scenario: 用户打开小红书搜索页
- **WHEN** 用户在浏览器中打开 `https://www.xiaohongshu.com/search_result?keyword=*` 页面
- **THEN** 扩展 content script 自动注入
- **AND** content script 可以通过 Main World 注入访问页面 DOM 和 `window.__INIT_PROPS__` SSR 数据

#### Scenario: 用户打开小红书笔记详情页
- **WHEN** 用户在浏览器中打开 `https://www.xiaohongshu.com/explore/*` 页面
- **THEN** 扩展 content script 自动注入
- **AND** content script 可以提取笔记详情数据

### Requirement: 小红书 API 请求拦截（被动获取）
扩展 SHALL 通过 Main World 注入拦截小红书页面发出的 API 请求和响应，被动捕获数据。

#### Scenario: 用户在小红书页面浏览时产生 API 请求
- **WHEN** 小红书页面通过 fetch 或 XHR 调用 `edith.xiaohongshu.com/api/sns/web/` 的 API
- **THEN** 扩展 Main World 脚本拦截请求和响应
- **AND** 提取响应中的笔记列表、笔记详情、评论等结构化数据
- **AND** 通过 postMessage → content script → background 链路将数据传递
- **AND** background 将数据缓存并同步到后端

#### Scenario: 拦截到的数据与后端同步
- **WHEN** 扩展拦截到有效的 XHS API 响应数据
- **THEN** background 将数据通过 HTTPS POST 同步到后端 `/market/extension-scrape-xhs` 端点
- **AND** 数据标记来源为 `"extension_intercepted"`

### Requirement: 小红书 SSR 数据提取
扩展 content script SHALL 能从小红书页面的 SSR 数据中提取结构化笔记信息。

#### Scenario: 小红书搜索页加载完成
- **WHEN** 用户打开小红书搜索页且页面加载完成
- **THEN** content script 通过 Main World 注入读取 `window.__INIT_PROPS__`
- **AND** 提取搜索结果列表中的笔记 ID、标题、作者、互动数据、标签等信息
- **AND** 将提取的数据通过 `chrome.runtime.sendMessage` 发送给 background script

#### Scenario: 小红书笔记详情页加载完成
- **WHEN** 用户打开小红书笔记详情页且页面加载完成
- **THEN** content script 提取笔记完整信息（标题、描述、图片、视频、标签、互动数据）
- **AND** 将数据发送给 background script

### Requirement: X-s / X-t 签名获取
扩展 SHALL 支持获取小红书 API 的 X-s / X-t 签名，用于主动 API 调用场景。

#### Scenario: 扩展需要主动调用小红书搜索 API
- **WHEN** 后端请求扩展抓取指定关键词的小红书搜索结果
- **THEN** 扩展通过 Main World 注入脚本调用小红书页面的签名函数生成 X-s / X-t
- **OR** 扩展从拦截到的真实请求中复用签名参数
- **AND** 使用签名后的完整参数发起 API 请求

#### Scenario: 签名获取失败
- **WHEN** 扩展无法获取有效的 X-s / X-t 签名
- **THEN** 扩展回退到 SSR 数据提取模式
- **AND** 记录警告日志

### Requirement: 扩展 Service Worker 小红书搜索 API 调用
扩展 background service worker SHALL 能使用用户真实 Cookie 和签名调用小红书搜索 API。

#### Scenario: 后端请求扩展抓取小红书市场数据
- **WHEN** 后端通过扩展通信通道请求抓取指定关键词的小红书搜索结果
- **THEN** 扩展 service worker 使用 `chrome.cookies.getAll` 获取小红书 Cookie
- **AND** 通过 Main World 注入获取 X-s / X-t 签名
- **AND** 使用 `fetch()` 调用小红书搜索 API（`/api/sns/web/v1/search/notes`）
- **AND** 将响应数据通过 HTTPS POST 同步到后端

#### Scenario: API 调用失败（签名无效/风控）
- **WHEN** 扩展调用小红书 API 返回非 200 状态码或空数据
- **THEN** 扩展回退到 content script 读取当前小红书页面的 SSR 数据
- **AND** 将可用数据同步到后端并标记数据来源

### Requirement: 小红书扩展抓取数据后端接收端点
后端 SHALL 提供 API 端点接收扩展提交的小红书市场热门数据。

#### Scenario: 扩展提交小红书抓取结果
- **WHEN** 扩展将抓取的小红书搜索结果 POST 到后端
- **THEN** 后端验证数据完整性
- **AND** 创建 `MarketHot` 记录，`hot_type` 标记为 `"xhs_extension_scraped"` 或 `"xhs_extension_intercepted"`
- **AND** 返回 201 Created

#### Scenario: 扩展提交的数据缺少必要字段
- **WHEN** 扩展提交的数据缺少 `keyword` 或 `notes` 列表为空
- **THEN** 后端返回 400 Bad Request

### Requirement: 分层降级抓取策略
扩展 SHALL 实现分层降级的小红书数据抓取策略，确保在各种条件下都能获取数据。

#### Scenario: 完整抓取流程
- **WHEN** 扩展收到抓取请求
- **THEN** 按以下优先级尝试：
  1. **请求拦截数据**（优先）：使用已缓存的拦截数据，零延迟
  2. **主动 API 调用**：使用签名 + Cookie 主动调用搜索 API
  3. **SSR 数据提取**：从当前小红书页面的 SSR 数据提取
  4. **DOM 解析**：解析页面 DOM 结构提取数据
- **AND** 每一层失败后自动降级到下一层
- **AND** 数据标记实际来源（`intercepted` / `api` / `ssr` / `dom`）

## MODIFIED Requirements

### Requirement: 市场数据抓取架构
系统支持三种市场数据获取方式（原仅后端 API 爬虫 + 抖音扩展抓取）：
1. **扩展抓取路径 - 抖音**（已有）：用户浏览器扩展在抖音页面内抓取数据
2. **扩展抓取路径 - 小红书**（新增）：用户浏览器扩展在小红书页面内抓取数据，支持请求拦截、主动 API 调用、SSR 提取、DOM 解析四种方式
3. **后端 API 爬虫路径**（降级）：后端通过 httpx 直接调用 API。当扩展不在线时使用，可能因签名缺失失败

## REMOVED Requirements
无移除需求。此变更纯增量，不破坏现有功能。
