# Intent Money OS 部署指南

本文档介绍如何在 Ubuntu 服务器上通过 Docker Compose 一键部署 Intent Money OS。

---

## 1. 服务器环境准备

### 1.1 系统要求

| 项目     | 最低要求       |
|--------|------------|
| 操作系统  | Ubuntu 20.04+ |
| CPU    | 2 核         |
| 内存    | 2 GB         |
| 磁盘    | 20 GB        |
| 网络    | 可访问外网       |

### 1.2 安装 Docker

```bash
# 更新包索引
sudo apt update

# 安装依赖
sudo apt install -y ca-certificates curl gnupg

# 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

### 1.3 防火墙配置

```bash
# 开放 80 端口（Nginx 反向代理）
sudo ufw allow 80/tcp

# 如果需要 HTTPS，同时开放 443
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 2. 一键部署步骤

### 2.1 克隆项目

```bash
git clone <your-repo-url> intent-money
cd intent-money
```

### 2.2 配置 .env 文件

```bash
# 从模板复制
cp backend/.env.example backend/.env

# 编辑配置（必须修改 SECRET_KEY 和 AI_API_KEY）
nano backend/.env
```

**必须修改的配置项：**

- `SECRET_KEY` — 替换为强随机字符串，用于 JWT 签名。可用以下命令生成：
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `AI_API_KEY` — 填入你的 OpenRouter API 密钥
- `ENV` — 生产环境设为 `production`

### 2.3 启动服务

```bash
cd docker
docker compose up -d --build
```

首次启动会构建镜像，耗时约 3-5 分钟。

### 2.4 验证服务状态

```bash
# 查看容器状态
docker compose ps

# 预期输出：两个服务均为 running / healthy
# NAME         STATUS
# backend      Up (healthy)
# nginx        Up

# 检查后端健康接口
curl http://localhost/health

# 检查后端 API
curl http://localhost/api/v1/auth/login

# 浏览器访问
# http://<服务器IP>
```

---

## 3. CDP 连接配置

CDP（Chrome DevTools Protocol）用于让后端控制本地 Chrome 浏览器，实现自动化操作（如发布内容到平台）。

### 3.1 本地 Chrome 启动

**Windows（PowerShell）：**

```powershell
.\scripts\start-chrome.ps1
```

**macOS / Linux：**

```bash
bash scripts/start-chrome.sh
```

脚本会以 `--remote-debugging-port=9222` 参数启动 Chrome，并使用独立的用户数据目录 `~/.intent-money/chrome-user-data`。

启动后访问 http://localhost:9222 可看到 Chrome 的调试页面。

### 3.2 内网穿透配置

由于后端运行在服务器上，Chrome 运行在本地，需要通过内网穿透将本地 9222 端口暴露给服务器。

#### 方案 A：frp

1. **服务端**（与 Intent Money OS 同一台服务器）：

   下载 frp 并编辑 `frps.toml`：

   ```toml
   bindPort = 7000
   auth.token = "your-frp-token"
   ```

   启动：

   ```bash
   ./frps -c frps.toml
   ```

2. **客户端**（本地机器）：

   下载 frp 并编辑 `frpc.toml`：

   ```toml
   serverAddr = "<服务器IP>"
   serverPort = 7000
   auth.token = "your-frp-token"

   [[proxies]]
   name = "cdp"
   type = "tcp"
   localIP = "127.0.0.1"
   localPort = 9222
   remotePort = 9222
   ```

   启动：

   ```bash
   ./frpc -c frpc.toml
   ```

3. 服务器上通过 `127.0.0.1:9222` 即可访问本地 Chrome。

#### 方案 B：cloudflared

1. **本地机器**安装 cloudflared：

   ```bash
   # macOS
   brew install cloudflared

   # Windows
   winget install Cloudflare.cloudflared
   ```

2. 建立隧道：

   ```bash
   cloudflared tunnel --url http://localhost:9222
   ```

3. 命令行会输出一个 `https://xxx.trycloudflare.com` 地址，将其作为 `CDP_DEBUG_HOST`。

### 3.3 配置 CDP_DEBUG_HOST 环境变量

编辑 `backend/.env`：

**frp 方案：**

```env
CDP_ENABLED=true
CDP_DEBUG_HOST=127.0.0.1
CDP_DEBUG_PORT=9222
```

**cloudflared 方案：**

```env
CDP_ENABLED=true
CDP_DEBUG_HOST=xxx.trycloudflare.com
CDP_DEBUG_PORT=443
CDP_DEBUG_SCHEME=https
```

修改后重启后端：

```bash
cd docker
docker compose restart backend
```

### 3.4 验证 CDP 连接

```bash
curl http://localhost/api/v1/cdp/health
```

返回正常状态即表示连接成功。

---

## 4. 环境变量说明

| 变量                     | 默认值                                        | 说明                          |
|------------------------|--------------------------------------------|-----------------------------|
| `DATABASE_URL`         | `sqlite+aiosqlite:///./intent_money.db`    | 数据库连接字符串                     |
| `SECRET_KEY`           | `your-secret-key-here`                     | JWT 签名密钥，生产环境必须修改            |
| `ALGORITHM`            | `HS256`                                    | JWT 加密算法                     |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `7`                                        | Token 过期天数                   |
| `AI_API_KEY`           | —                                          | OpenRouter API 密钥            |
| `AI_BASE_URL`          | `https://openrouter.ai/api/v1`             | AI API 地址                    |
| `AI_MODEL`             | `deepseek/deepseek-chat-v3-0324:free`      | AI 模型标识                      |
| `XHS_COOKIE`           | —                                          | 小红书平台 Cookie（可选）             |
| `DOUYIN_COOKIE`        | —                                          | 抖音平台 Cookie（可选）             |
| `SMS_ENABLED`          | `false`                                    | 是否启用短信验证                     |
| `SMS_GATEWAY`          | —                                          | 短信网关地址                       |
| `SMS_ACCESS_KEY`       | —                                          | 短信服务 AccessKey               |
| `SMS_SECRET_KEY`       | —                                          | 短信服务 SecretKey               |
| `SMS_SIGN_NAME`        | —                                          | 短信签名名称                       |
| `SMS_TEMPLATE_CODE`    | —                                          | 短信模板编码                       |
| `SCRAPER_ENABLED`      | `true`                                     | 是否启用数据爬取                     |
| `SCRAPER_TIMEOUT`      | `30`                                       | 爬取超时时间（秒）                    |
| `SENTIMENT_ENABLED`    | `true`                                     | 是否启用情感分析                     |
| `AUTO_PUBLISH_ENABLED` | `false`                                    | 是否启用自动发布                     |
| `SOCIAL_AUTO_UPLOAD_PATH` | —                                          | social-auto-upload 模块路径（可选） |
| `COOKIE_DIR`           | `cookies`                                  | Cookie 存储目录                  |
| `COOKIE_EXPIRE_DAYS`   | `7`                                        | Cookie 过期天数                  |
| `CDP_ENABLED`          | `false`                                    | 是否启用 CDP 浏览器控制               |
| `CDP_DEBUG_HOST`       | `127.0.0.1`                                | CDP 调试地址                     |
| `CDP_DEBUG_PORT`       | `9222`                                     | CDP 调试端口                     |
| `CDP_DEBUG_SCHEME`     | `http`                                     | CDP 连接协议（`http` 或 `https`，cloudflared 穿透用 `https`） |
| `DEV_MODE`             | `false`                                    | 开发模式开关，开启后无限换条               |
| `ENV`                  | `development`                              | 运行环境：`development` 或 `production` |

---

## 5. 常见问题排查

### 容器启动失败

**症状：** `docker compose up -d` 后容器退出或不断重启。

**排查步骤：**

```bash
# 查看容器日志
docker compose logs backend
docker compose logs nginx

# 查看具体退出原因
docker compose ps -a
```

**常见原因：**

- 端口被占用：`80` 端口已被其他程序占用，使用 `sudo lsof -i :80` 检查。
- `.env` 文件缺失：确认 `backend/.env` 存在且格式正确。
- 构建失败：检查网络连接，确保能拉取 Docker 基础镜像和 pip/npm 依赖。

### CDP 连接失败

**症状：** `/api/v1/cdp/health` 返回错误或超时。

**排查步骤：**

1. 确认本地 Chrome 已启动并开启调试端口：
   ```bash
   # 本地机器
   curl http://localhost:9222/json/version
   ```

2. 确认内网穿透正常：
   ```bash
   # 服务器上测试
   curl http://<CDP_DEBUG_HOST>:<CDP_DEBUG_PORT>/json/version
   ```

3. 确认 `.env` 中 `CDP_ENABLED=true` 且 `CDP_DEBUG_HOST` / `CDP_DEBUG_PORT` 配置正确。

4. 重启后端使配置生效：
   ```bash
   docker compose restart backend
   ```

### 前端页面空白

**症状：** 浏览器访问显示空白页。

**排查步骤：**

1. 打开浏览器开发者工具（F12），查看 Console 和 Network 中的错误。
2. 检查 Nginx 配置是否正确代理前端和后端：
   ```bash
   docker compose exec nginx cat /etc/nginx/conf.d/default.conf
   ```
3. 确认前端构建成功：
   ```bash
   docker compose logs nginx
   ```

### 数据库迁移问题

**症状：** 后端启动报错 `no such table` 或 Alembic 相关错误。

**排查步骤：**

1. 手动执行迁移：
   ```bash
   docker compose exec backend uv run alembic upgrade head
   ```

2. 查看当前迁移状态：
   ```bash
   docker compose exec backend uv run alembic current
   ```

3. 如果迁移文件冲突，查看迁移历史：
   ```bash
   docker compose exec backend uv run alembic history
   ```

4. 数据库文件位于 Docker volume 中，如需重置：
   ```bash
   # ⚠️ 这将删除所有数据
   docker compose down -v
   docker compose up -d --build
   ```

   > 注意：`entrypoint.sh` 会在容器启动时自动执行 `alembic upgrade head`，通常不需要手动迁移。
