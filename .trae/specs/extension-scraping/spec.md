# 扩展增强抓取能力 Spec

## Why
移除 CDP 模块后，后端通过 httpx 直接调用抖音内部 API 返回 404，`market_hots` 表为空，任务生成无法参考最新市场热门内容。浏览器扩展已具备 Cookie 获取和同步能力，且拥有 `*.douyin.com` 的 `host_permissions`，可以扩展为在用户浏览器内完成数据抓取，绕过后端面临的反爬和 API 失效问题。

## What Changes
- **新增** 扩展抖音页面 content script 注入（`manifest.json` 添加 `content_scripts` 匹配 `*://*.douyin.com/*`）
- **新增** 扩展 background.js 中抖音搜索 API 调用逻辑（Service Worker fetch + 真实 Cookie）
- **新增** 扩展 content script 读取抖音页面 SSR 数据（`__INIT_PROPS__`）的逻辑
- **新增** 扩展与后端的数据同步 API（将抓取结果 POST 到后端）
- **新增** 后端 API 端点接收扩展提交的市场数据
- **修改** `market_service.py`：支持从扩展提交的数据创建 MarketHot 记录
- **修改** `manifest.json`：添加 `scripting` 权限，扩展抖音页面 content script 匹配规则
- **修改** `background.js`：添加搜索抓取消息处理器
- **修改** `content.js`：添加抖音页面数据提取逻辑

## Impact
- Affected specs: 市场数据抓取架构（从后端直接调用 API → 扩展浏览器内抓取 + 后端存储）
- Affected code: `extension/manifest.json`、`extension/background.js`、`extension/content.js`、`backend/app/api/v1/market.py`、`backend/app/services/market_service.py`

## ADDED Requirements

### Requirement: 扩展抖音页面 Content Script 注入
扩展 SHALL 在抖音页面注入 content script，具备读取页面 DOM 和 SSR 数据的能力。

#### Scenario: 用户打开抖音搜索页
- **WHEN** 用户在浏览器中打开 `https://www.douyin.com/search/*` 页面
- **THEN** 扩展 content script 自动注入
- **AND** content script 可以访问页面 DOM 和 `window.__INIT_PROPS__` SSR 数据

### Requirement: 扩展 Service Worker 抖音搜索 API 调用
扩展 background service worker SHALL 能使用用户真实 Cookie 调用抖音搜索 API。

#### Scenario: 后端请求扩展抓取市场数据
- **WHEN** 后端通过扩展通信通道请求抓取指定关键词的搜索结果
- **THEN** 扩展 service worker 使用 `chrome.cookies.getAll` 获取抖音 Cookie
- **AND** 使用 `fetch()` 调用抖音搜索 API（`/aweme/v1/search/item/`）
- **AND** 将响应数据通过 HTTPS POST 同步到后端

#### Scenario: API 调用失败（404/签名过期）
- **WHEN** 扩展调用抖音 API 返回非 200 状态码
- **THEN** 扩展回退到 content script 读取当前抖音页面的 SSR 数据
- **AND** 将可用数据同步到后端并标记数据来源

### Requirement: 扩展抓取数据后端接收端点
后端 SHALL 提供 API 端点接收扩展提交的市场热门数据。

#### Scenario: 扩展提交抓取结果
- **WHEN** 扩展将抓取的抖音搜索结果 POST 到后端
- **THEN** 后端验证数据完整性
- **AND** 创建 `MarketHot` 记录，`hot_type` 标记为 `"extension_scraped"`
- **AND** 返回 201 Created

#### Scenario: 扩展提交的数据缺少必要字段
- **WHEN** 扩展提交的数据缺少 `keyword` 或 `platform_id`
- **THEN** 后端返回 400 Bad Request

### Requirement: 扩展主动抓取触发机制
扩展 SHALL 支持后端主动触发抓取任务。

#### Scenario: 后端定时任务触发扩展抓取
- **WHEN** 后端定时任务需要更新市场数据
- **THEN** 后端通过 WebSocket 或轮询机制通知扩展执行抓取
- **AND** 扩展在用户浏览器空闲时执行抓取
- **AND** 抓取结果同步到后端

#### Scenario: 用户浏览器未运行或扩展未安装
- **WHEN** 后端触发抓取但扩展不在线
- **THEN** 后端跳过本次抓取，使用已有数据或默认模板
- **AND** 记录日志标记扩展离线

### Requirement: 抖音页面 SSR 数据提取
扩展 content script SHALL 能从抖音搜索页的 SSR 数据中提取结构化视频信息。

#### Scenario: 抖音搜索页加载完成
- **WHEN** 用户打开抖音搜索页且页面加载完成
- **THEN** content script 通过 Main World 注入读取 `window.__INIT_PROPS__`
- **AND** 提取搜索结果列表中的视频 ID、标题、作者、统计数据、标签等信息
- **AND** 将提取的数据通过 `chrome.runtime.sendMessage` 发送给 background script

### Requirement: X-Bogus 签名处理
扩展 SHALL 处理抖音 API 的 X-Bogus 签名要求。

#### Scenario: 抖音 API 需要 X-Bogus 签名
- **WHEN** 扩展调用抖音内部 API 时需要 X-Bogus 参数
- **THEN** 扩展通过 Main World 注入脚本调用抖音页面的签名函数
- **OR** 扩展拦截浏览器发出的真实请求，复用签名参数
- **AND** 使用签名后的完整参数发起 API 请求

#### Scenario: 签名获取失败
- **WHEN** 扩展无法获取有效的 X-Bogus 签名
- **THEN** 扩展回退到 SSR 数据提取模式
- **AND** 记录警告日志

## MODIFIED Requirements

### Requirement: 市场数据抓取架构
系统支持两种市场数据获取方式（原仅后端 API 爬虫）：
1. **扩展抓取路径**（优先）：用户浏览器扩展在抖音页面内抓取数据，通过 HTTPS 同步到后端。优势：真实浏览器环境 + 自动 Cookie 管理 + 低反爬风险。
2. **后端 API 爬虫路径**（降级）：后端通过 httpx 直接调用抖音 API。当扩展不在线时使用，可能因反爬措施失败。

## REMOVED Requirements

无移除需求。此变更纯增量，不破坏现有功能。
