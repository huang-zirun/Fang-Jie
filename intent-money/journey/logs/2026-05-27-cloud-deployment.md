# 云服务器部署实现

## 日期
2026-05-27

## 概述
将 Intent Money OS 从本地 Windows 环境部署到 Ubuntu 云服务器。核心挑战是 CDP 爬取功能依赖本地已登录的 Chrome 浏览器，通过内网穿透（frp/cloudflared）连接本地 Chrome。

## 架构决策

### 方案选择：本地 Chrome + 内网穿透
- **原因**：用户只需要爬取功能，本地电脑 24 小时开机，Cookie 可保持一段时间
- **替代方案**：服务器 Chrome + noVNC（资源占用多）、混合模式（配置复杂）

### Docker 架构
- 从 3 服务（backend + frontend + nginx）简化为 2 服务（backend + nginx）
- Frontend 构建产物直接打入 Nginx 镜像，不再需要独立的 frontend 容器
- 数据库路径从 `/app/intent_money.db` 改为 `/app/data/intent_money.db`，通过 Docker volume 持久化

### CDP 远程连接
- 新增 `CDP_DEBUG_SCHEME` 配置项，支持 HTTPS（cloudflared 穿透需要）
- CdpBrowser 新增 `scheme` 参数，WebSocket 自动选择 ws/wss
- 新增 `/api/v1/cdp/health` 端点，检查 CDP 连通性

## 变更文件清单

### 新增文件
| 文件 | 说明 |
|------|------|
| `backend/Dockerfile` | Python 3.11-slim + uv，非 root 用户运行 |
| `backend/entrypoint.sh` | 启动脚本：alembic 迁移 + uvicorn |
| `backend/.dockerignore` | Docker 构建排除文件 |
| `frontend/Dockerfile` | 多阶段构建：Node 构建 + Nginx 托管 |
| `frontend/.dockerignore` | Docker 构建排除文件 |
| `backend/app/api/v1/cdp.py` | CDP 健康检查 API 端点 |
| `scripts/start-chrome.ps1` | Windows Chrome 远程调试启动脚本 |
| `scripts/start-chrome.sh` | macOS/Linux Chrome 远程调试启动脚本 |
| `scripts/frpc.ini` | frp 内网穿透配置示例 |
| `scripts/cloudflared-config.yml` | cloudflared 内网穿透配置示例 |
| `docs/deploy.md` | 部署文档 |

### 修改文件
| 文件 | 变更 |
|------|------|
| `docker/docker-compose.yml` | 重构为生产模式：2 服务、无 volume 挂载、healthcheck、restart 策略 |
| `docker/nginx.conf` | 增强：静态资源托管、Gzip、安全头部、缓存策略、SPA 回退 |
| `backend/app/config.py` | 新增 `CDP_DEBUG_SCHEME` 配置项 |
| `backend/app/api/v1/router.py` | 注册 cdp_router |
| `backend/app/services/platform_scraper/cdp_browser.py` | 新增 `scheme` 参数，支持 HTTPS/WSS |
| `backend/app/services/platform_scraper/cdp_douyin_scraper.py` | 使用 settings 配置 CDP 连接 |
| `backend/app/services/platform_scraper/cdp_xhs_scraper.py` | 使用 settings 配置 CDP 连接 |
| `backend/app/services/cdp_publisher.py` | 新增 `scheme` 参数 |
| `backend/.env.example` | 新增 CDP_DEBUG_SCHEME |

## 关键技术细节

### Nginx 安全头部
Nginx 的 `add_header` 在 location 块中会覆盖父级所有 `add_header`，因此每个 location 块都需要重复安全头部。

### Docker Healthcheck
Backend 使用 Python 内置 `urllib.request` 进行健康检查，避免在 slim 镜像中安装 curl。

### 数据库持久化
Docker volume `db_data` 挂载到 `/app/data`，DATABASE_URL 在 docker-compose.yml 中覆盖为 `sqlite+aiosqlite:///./data/intent_money.db`。

## 待验证
- [ ] 在实际 Ubuntu 服务器上执行 `docker compose up -d --build`
- [ ] 验证前端页面和 API 正常
- [ ] 验证 frp 穿透后 CDP 连接
- [ ] 验证 cloudflared 穿透后 CDP 连接
