# 完全移除 CDP 模块 Spec

## Why
CDP（Chrome DevTools Protocol）路径依赖服务器本机 Chrome 浏览器，架构复杂、维护成本高，且浏览器扩展路径已可覆盖所有核心功能。移除 CDP 可简化架构、减少依赖、降低部署复杂度。

## What Changes
- **删除** CDP 核心模块：`cdp_browser.py`、`cdp_qrcode_login.py`、`cdp_publisher.py`、`cdp_xhs_scraper.py`、`cdp_douyin_scraper.py`
- **删除** CDP API 端点：`api/v1/cdp.py` 及其路由注册
- **删除** Chrome 启动脚本：`start-chrome.sh`、`start-chrome.ps1`、`frpc.ini`
- **删除** CDP 相关测试：`test_cdp.py`、`test_cdp_content_generation.py`
- **修改** `config.py`：移除 `CDP_ENABLED`、`CDP_DEBUG_HOST`、`CDP_DEBUG_PORT`、`CDP_DEBUG_SCHEME` 配置项
- **修改** `accounts.py`：扫码登录直接走 Playwright 路径，移除 CDP 优先降级逻辑
- **修改** `scraper.py` / `scraper_xhs.py`：移除 CDP 爬虫选择逻辑，统一使用 Playwright/API 爬虫
- **修改** `auto_publisher.py`：移除 CDP 发布路径，仅保留 sau CLI 方案
- **修改** `per_user_scraper.py`：移除 CDP 共享爬虫创建逻辑
- **修改** `market_service.py`：移除 CDP 爬虫引用
- **修改** `snapshot_scheduler.py`：移除 CDP 浏览器数据抓取逻辑
- **修改** `snapshots.py`：移除 CDP fetch 端点
- **修改** `platform_scraper/__init__.py`：移除 CDP 导出
- **修改** `server.py`（两处）：移除 Chrome CDP 启动逻辑
- **修改** `docker-compose.yml`：移除 CDP 环境变量
- **修改** `pyproject.toml`：移除 `websockets` 依赖
- **修改** `deploy.md`：移除 CDP 连接配置章节
- **更新** `journey/design.md`：移除 CDP 相关架构描述
- **更新** `AGENTS.md`：移除 CDP 技术栈描述
- **BREAKING** 移除 `/api/v1/cdp/health` 端点
- **BREAKING** 移除 `CDP_ENABLED` / `CDP_DEBUG_HOST` / `CDP_DEBUG_PORT` / `CDP_DEBUG_SCHEME` 环境变量
- **BREAKING** 移除 `POST /tasks/{id}/snapshots/fetch` 端点（CDP 专用）

## Impact
- Affected specs: 账号绑定三路径架构（从三路径变为两路径：扩展 + Playwright）
- Affected code: 后端 15+ 文件，脚本 3 文件，文档 2 文件，测试 2 文件
- 前端 `AccountManage.vue` 无需改动（扫码登录 API 接口不变，后端内部直接走 Playwright）

## ADDED Requirements

### Requirement: Playwright 直连扫码登录
扫码登录请求 SHALL 直接使用 Playwright 路径，不再尝试 CDP 优先降级。

#### Scenario: 用户请求扫码登录
- **WHEN** 用户调用 `POST /accounts/{platform}/qrcode`
- **THEN** 系统直接启动 Playwright 无头浏览器完成扫码登录
- **AND** 不再检查 CDP 可用性

### Requirement: 快照手动录入
快照数据 SHALL 仅支持手动录入，移除 CDP 自动抓取。

#### Scenario: 用户录入快照
- **WHEN** 用户调用 `POST /tasks/{id}/snapshots`
- **THEN** 系统保存手动提交的快照数据

### Requirement: 自动发布仅走 sau CLI
自动发布 SHALL 仅使用 sau CLI 方案，移除 CDP 发布路径。

#### Scenario: 用户触发自动发布
- **WHEN** 用户触发自动发布
- **THEN** 系统使用 sau CLI 发布
- **AND** 不再尝试 CDP 发布

## MODIFIED Requirements

### Requirement: 账号绑定路径架构
系统支持两条账号绑定路径（原三条）：
1. **浏览器扩展路径**：最佳用户体验，支持一键获取和后台自动同步。
2. **Playwright 路径**：未安装扩展时的降级方案，启动无头浏览器完成扫码登录。

## REMOVED Requirements

### Requirement: CDP 路径扫码登录
**Reason**: CDP 依赖服务器本机 Chrome，架构复杂且浏览器扩展已覆盖核心功能。
**Migration**: 扫码登录统一走 Playwright 路径。

### Requirement: CDP 数据抓取
**Reason**: CDP 爬虫依赖服务器 Chrome，维护成本高。Playwright/API 爬虫已满足需求。
**Migration**: 统一使用 Playwright/API 爬虫。

### Requirement: CDP 自动发布
**Reason**: CDP 发布依赖服务器 Chrome 登录状态，不可靠。sau CLI 方案更稳定。
**Migration**: 自动发布仅走 sau CLI。

### Requirement: CDP 快照自动抓取
**Reason**: 依赖 CDP 浏览器连接，不可靠。手动录入更可控。
**Migration**: 快照仅支持手动录入。

### Requirement: CDP 健康检查端点
**Reason**: CDP 模块整体移除。
**Migration**: 无需替代。
