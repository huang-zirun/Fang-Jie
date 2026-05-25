# CDP 浏览器自动化抓取服务集成 - 2026-05-25

## 背景

原有爬虫直接调用平台 Web API（小红书 `/api/sns/web/v1/search/notes`、抖音 `/aweme/v1/search/item/`），依赖手动配置 Cookie。Cookie 过期后完全无法抓取数据。

## 方案

通过 Chrome DevTools Protocol (CDP) 连接已登录的 Chrome 浏览器，直接从页面 DOM 提取数据。无需 Cookie，只要浏览器保持登录态即可。

## 新增文件

- `app/services/platform_scraper/cdp_browser.py` — CDP 浏览器管理类
  - 封装 websockets + httpx 连接 Chrome DevTools Protocol
  - 提供 `navigate(url)` / `evaluate(js)` / `get_page_text()` / `check_health()` 方法
  - 单例模式维护持久连接，自动检测连接存活
- `app/services/platform_scraper/cdp_xhs_scraper.py` — 小红书 CDP 爬虫
  - 继承 `BasePlatformScraper`
  - 导航搜索页后用 CSS 选择器提取笔记数据（`.note-item` → `.footer .title` / `.author .name` / `.like-wrapper .count`）
  - 兼容 `.footer` 和 `.card-bottom-wrapper` 两种卡片结构
- `app/services/platform_scraper/cdp_douyin_scraper.py` — 抖音 CDP 爬虫
  - 继承 `BasePlatformScraper`
  - 导航搜索页后用正则解析视频数据（时长+点赞+标题+作者+时间）

## 改动文件

- `app/config.py` — 新增 `CDP_ENABLED` / `CDP_DEBUG_HOST` / `CDP_DEBUG_PORT` 配置
- `app/services/platform_scraper/__init__.py` — 导出 CDP 爬虫类
- `app/api/v1/scraper.py` — 路由层根据 `CDP_ENABLED` 切换爬虫实例
- `app/api/v1/scraper_xhs.py` — 同上
- `app/services/market_service.py` — 定时任务也切换为 CDP 爬虫
- `pyproject.toml` — 添加 `websockets>=12.0` 依赖
- `.env` — 新增 CDP 配置项（默认启用）
- `journey/design.md` — 更新设计文档
- `intent-money/journey/design.md` — 更新设计文档

## Chrome 启动方式

```bash
# 使用已有 profile（保留登录态）
chrome.exe --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1

# 临时 profile（需扫码登录）
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

## 兼容性设计

- `CDP_ENABLED=false`（默认）→ 走原有 API 爬虫逻辑，零影响
- `CDP_ENABLED=true` → 走 CDP 模式
- CDP 连接失败时返回空列表，不抛异常，下游降级处理

## 验证结果

- `GET /api/v1/scraper/health` → `{"douyin": {"healthy": true, "cdp": true}, "xhs": {"healthy": true, "cdp": true}}`
- `POST /api/v1/scraper/xhs/search?keyword=袜子&limit=5` → 返回 5 条笔记（标题、作者、点赞、链接）
- `POST /api/v1/scraper/douyin/search?keyword=袜子&limit=5` → 返回 5 个视频（标题、作者、点赞、时长）
- 直接调用 CDP 爬虫类验证：小红书 5 条、抖音 5 条，数据格式与原有格式一致

## 新增 server.py 一键启动脚本

`backend/server.py` — 整合 Chrome CDP 启动 + 后端启动：
- `python server.py` — 自动检测/启动 Chrome CDP，然后启动后端
- `python server.py --no-chrome` — 跳过 Chrome 启动（CDP 已手动启动）
- `python server.py --api-mode` — API 模式（不依赖 Chrome）
- 优先使用 `uv run uvicorn`，回退到 `python -m uvicorn`
- Ctrl+C 同时停止 Chrome 和后端

## 已知问题

- 小红书部分笔记标题为空（纯图片/视频笔记，DOM 结构不同）
- 抖音视频 ID 为 UUID 占位（CDP 模式不暴露真实 video_id，需要额外提取）
