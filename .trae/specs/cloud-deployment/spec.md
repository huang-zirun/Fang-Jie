# 云服务器部署 Spec

## Why
项目当前运行在本地 Windows 环境，需要部署到 Ubuntu 云服务器上，让应用可以通过公网访问。核心挑战是 CDP（Chrome DevTools Protocol）爬取功能依赖本地已登录的 Chrome 浏览器，云服务器上没有 Chrome，需要通过内网穿透连接本地 Chrome。

## What Changes
- 新增 Backend Dockerfile（基于 Python 3.11 + uv）
- 新增 Frontend Dockerfile（多阶段构建：Node 构建 + Nginx 托管）
- 重构 docker-compose.yml 为生产模式（去掉开发用的 volume mounts 和 --reload）
- 更新 nginx.conf 为生产级配置（HTTPS 准备、WebSocket 支持、静态资源缓存）
- 修改后端 CDP 配置，支持通过环境变量指定远程 Chrome 地址（穿透地址）
- 新增本地 Chrome 启动脚本（Windows），一键开启远程调试模式
- 新增内网穿透配置指南（frp + cloudflared 两种方案）
- 新增部署文档（一键部署脚本、环境变量说明）

## Impact
- Affected specs: intent-money-mvp（部署架构变更）
- Affected code:
  - `backend/app/config.py`（CDP 配置项）
  - `docker/docker-compose.yml`（重构）
  - `docker/nginx.conf`（增强）
  - 新增 `backend/Dockerfile`
  - 新增 `frontend/Dockerfile`
  - 新增 `scripts/start-chrome.ps1`（本地 Chrome 启动脚本）
  - 新增 `scripts/start-chrome.sh`（本地 Chrome 启动脚本，macOS/Linux）

## ADDED Requirements

### Requirement: Backend Docker 镜像
系统 SHALL 提供 Backend Dockerfile，基于 Python 3.11 slim 镜像，使用 uv 安装依赖，以非 root 用户运行 uvicorn。

#### Scenario: 构建并运行 Backend 容器
- **WHEN** 执行 `docker compose build backend`
- **THEN** 成功构建镜像，包含所有 Python 依赖
- **WHEN** 执行 `docker compose up backend`
- **THEN** 后端服务在 8000 端口启动，健康检查通过

### Requirement: Frontend Docker 镜像
系统 SHALL 提供 Frontend Dockerfile，采用多阶段构建：第一阶段用 Node 构建静态资源，第二阶段用 Nginx 托管。

#### Scenario: 构建并运行 Frontend 容器
- **WHEN** 执行 `docker compose build frontend`
- **THEN** 成功构建镜像，产出 Nginx 静态资源托管镜像
- **WHEN** 执行 `docker compose up frontend`
- **THEN** 前端页面可通过 Nginx 访问

### Requirement: 生产级 Docker Compose
系统 SHALL 提供生产级 docker-compose.yml，不挂载源码目录，不使用 --reload，配置重启策略。

#### Scenario: 一键部署
- **WHEN** 在云服务器上执行 `docker compose up -d`
- **THEN** 所有服务（backend、frontend-nginx）启动，通过 80 端口可访问应用

### Requirement: CDP 远程连接支持
系统 SHALL 支持通过环境变量 `CDP_DEBUG_HOST` 和 `CDP_DEBUG_PORT` 配置远程 Chrome 地址，使后端能通过内网穿透连接本地 Chrome。

#### Scenario: 连接本地 Chrome
- **GIVEN** 本地 Chrome 以 `--remote-debugging-port=9222` 启动
- **AND** 内网穿透工具将本地 9222 端口映射为 `tunnel.example.com:9222`
- **WHEN** 设置环境变量 `CDP_DEBUG_HOST=tunnel.example.com`
- **THEN** 后端 CDP 连接成功，爬取功能正常工作

#### Scenario: Chrome 不可用时优雅降级
- **WHEN** 本地 Chrome 未启动或穿透断线
- **THEN** 后端健康检查返回 CDP 不可用状态，爬取 API 返回明确错误信息，其他功能不受影响

### Requirement: 本地 Chrome 启动脚本
系统 SHALL 提供一键启动脚本，以远程调试模式启动 Chrome，并自动加载用户数据目录（保持登录状态）。

#### Scenario: Windows 一键启动
- **WHEN** 在 Windows 上运行 `scripts/start-chrome.ps1`
- **THEN** Chrome 以 `--remote-debugging-port=9222 --user-data-dir=...` 启动

### Requirement: 内网穿透配置指南
系统 SHALL 提供 frp 和 cloudflared 两种内网穿透方案的配置说明和示例配置文件。

#### Scenario: 使用 frp 穿透
- **GIVEN** frp 服务端已部署
- **WHEN** 按照指南配置 frpc.ini
- **THEN** 本地 9222 端口可通过公网访问

#### Scenario: 使用 cloudflared 穿透
- **WHEN** 按照指南运行 cloudflared tunnel
- **THEN** 本地 9222 端口可通过 Cloudflare 域名访问

## MODIFIED Requirements

### Requirement: Docker Compose 配置
原 docker-compose.yml 为开发模式（挂载源码、--reload、独立 frontend 容器）。修改为生产模式：
- 去掉源码挂载和 --reload
- Frontend 构建产物由 Nginx 直接托管（不再需要独立 frontend 容器）
- 添加 restart: unless-stopped
- 添加环境变量配置（.env 文件）
- Nginx 同时托管前端静态资源和代理后端 API

### Requirement: Nginx 配置
原 nginx.conf 仅为基本反向代理。增强为：
- 前端静态资源直接由 Nginx 托管（不再代理到 frontend 容器）
- API 请求代理到 backend 容器
- WebSocket 支持（SSE 长连接）
- 静态资源缓存策略
- Gzip 压缩
- 安全头部（X-Frame-Options, X-Content-Type-Options 等）

### Requirement: CDP 配置项
原 `CDP_DEBUG_HOST` 默认值为 `127.0.0.1`。修改为支持远程地址：
- `CDP_DEBUG_HOST` 默认值保持 `127.0.0.1`（本地开发兼容）
- 新增 `CDP_DEBUG_HOST` 环境变量说明文档
- CdpBrowser 的 `_cdp_base` 属性已支持 host:port 格式，无需代码修改

## REMOVED Requirements
无
