# 小红书扩展实时数据抓取实施日志

**日期**: 2026-06-03
**类型**: 功能开发
**状态**: 已完成

## 背景

后端 `XhsScraper` 通过 httpx 直接调用小红书 API 时缺少 X-s / X-t 签名头，导致请求被拒绝或返回空数据。浏览器扩展已具备小红书 Cookie 获取能力，可以扩展为在用户浏览器内完成数据抓取，利用真实浏览器环境绕过签名校验。

## 研究发现

### 小红书 API 端点
- 搜索 API: `POST https://edith.xiaohongshu.com/api/sns/web/v1/search/notes`
- 笔记详情: `POST https://edith.xiaohongshu.com/api/sns/web/v1/feed`
- 评论 API: `GET https://edith.xiaohongshu.com/api/sns/web/v2/comment/page`

### 反爬措施
- **X-s / X-t 签名**: 最核心的反爬机制，每个 API 请求必须携带
- **签名算法特征**: 经过混淆处理，位置不固定，定期更新
- **Cookie 要求**: `web_session` 是核心登录态 Cookie
- **速率限制**: 同一 IP 短时间内大量请求会触发风控

### SSR 数据
- 小红书使用 React SSR，数据注入方式为 `window.__INIT_PROPS__`
- 搜索结果页、笔记详情页、用户主页都有 SSR 数据

## 实施内容

### 新增文件
1. `extension/xhs_main_world.js` — Main World 脚本
   - SSR 数据提取 (`window.__INIT_PROPS__`)
   - fetch/XHR 请求拦截（monkey-patch）
   - X-s/X-t 签名函数定位和调用
   - 通过 `postMessage` 与 content script 通信

2. `extension/xhs_content.js` — Content Script
   - Main World 脚本注入
   - 消息桥接（Main World ↔ Content Script ↔ Background）
   - DOM 解析降级
   - 页面加载自动提取 SSR 数据

### 修改文件
1. `extension/manifest.json`
   - 添加小红书 content_scripts 匹配规则
   - 添加 `web_accessible_resources` 暴露 Main World 脚本

2. `extension/background.js`
   - 新增 6 个消息处理器:
     - `SCRAPE_XHS_SEARCH`: 四层降级抓取
     - `XHS_INTERCEPTED_DATA`: 拦截数据缓存
     - `XHS_SIGNATURE_CAPTURED`: 签名缓存
     - `XHS_SSR_DATA`: 自动提取数据处理
     - `CHECK_XHS_TAB`: 标签页状态查询
     - `OPEN_XHS_SEARCH`: 打开搜索页

3. `backend/app/schemas/market_hot.py`
   - 新增 `XhsNoteItem` schema
   - 新增 `XhsExtensionScrapeData` schema

4. `backend/app/api/v1/market.py`
   - 新增 `POST /market/extension-scrape-xhs` 端点

5. `backend/app/services/market_service.py`
   - 新增 `scrape_xhs_via_extension()` 函数

## 四层降级策略

| 层级 | 方式 | 可靠性 | 说明 |
|------|------|--------|------|
| 1 | 请求拦截 | 最高 | 被动捕获用户浏览时的 API 响应，零签名问题 |
| 2 | 主动 API | 中 | 需要获取 X-s/X-t 签名，签名函数位置不固定 |
| 3 | SSR 提取 | 中 | 只能获取首屏数据，无法翻页 |
| 4 | DOM 解析 | 低 | 数据不完整，作为最后降级 |

## 缺陷修复

代码审查后发现并修复了 7 个缺陷：

| 编号 | 位置 | 描述 |
|------|------|------|
| BUG-1 | `XHS_INTERCEPTED_DATA` | 从 `message` 顶层解构，但数据在 `message.data` 内部 |
| BUG-2 | `XHS_SIGNATURE_CAPTURED` | 签名数据路径错误，键名为 `"X-s"`/`"X-t"` |
| BUG-3 | `SCRAPE_XHS_SEARCH` Layer 3 | 检查 `ssrResult.notes`，但实际字段名是 `searchResults` |
| BUG-4 | `SCRAPE_XHS_SEARCH` Layer 2 | 签名请求缺少 URL 参数，响应字段名不匹配 |
| BUG-5 | `background.js` | 缺少 `XHS_SSR_DATA` 处理器，自动提取数据被丢弃 |
| BUG-6 | `xhs_main_world.js` | 只拦截 fetch，缺少 XHR 拦截 |
| BUG-7 | `market.py` | `hot_type` 格式与清单规格不一致 |

## 关键技术决策

1. **请求拦截作为最优先方案**: 小红书签名比抖音更复杂，请求拦截是最可靠的绕过方式
2. **Main World 注入方式**: 使用 `web_accessible_resources` + `<script src>` 注入，而非 `chrome.scripting.executeScript`（content_scripts 配置中不支持 `world: "MAIN"`）
3. **消息来源标识**: 使用 `source: "intent-money-xhs"` 和 `source: "intent-money-xhs-content"` 区分方向
4. **缓存策略**: 拦截数据缓存 10 分钟，签名缓存 5 分钟

## 后续工作

- [ ] 端到端测试：在小红书搜索页验证 SSR 数据提取
- [ ] 端到端测试：验证请求拦截功能
- [ ] 端到端测试：验证签名获取和 API 调用
- [ ] 前端集成：添加触发扩展抓取的 UI 入口

## 参考

- 规范文档: `.trae/specs/xhs-extension-scraping/spec.md`
- 任务列表: `.trae/specs/xhs-extension-scraping/tasks.md`
- 检查清单: `.trae/specs/xhs-extension-scraping/checklist.md`
- 抖音实现参考: `extension/douyin_content.js`
