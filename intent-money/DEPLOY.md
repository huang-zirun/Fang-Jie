# Intent Money OS 生产部署指南

域名：`trades.zzy88.com`

---

## 服务器要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Ubuntu 20.04+ |
| CPU | 2 核 |
| 内存 | 2 GB |
| 磁盘 | 20 GB |
| 网络 | 可访问外网 |

---

## 1. 服务器初始化

### 1.1 安装 Docker

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

### 1.2 防火墙配置

```bash
# 开放 80 端口
sudo ufw allow 80/tcp

# 启用防火墙
sudo ufw enable
sudo ufw status
```

---

## 2. 项目部署

### 2.1 上传项目到服务器

**方式一：通过 Git 克隆**

```bash
cd ~
git clone <你的仓库地址> intent-money
cd intent-money
```

**方式二：本地打包上传**

```bash
# 在本地项目根目录执行，排除不需要的文件
tar -czvf intent-money.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  intent-money/

# 上传到服务器（使用 scp 或 ftp）
scp intent-money.tar.gz root@<服务器IP>:~/

# 在服务器上解压
ssh root@<服务器IP>
tar -xzvf intent-money.tar.gz
cd intent-money
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置
nano backend/.env
```

**必须修改的配置项：**

```env
# 生成强随机密钥（用于 JWT 签名）
# 执行：python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=你的随机密钥

# OpenRouter API 密钥
AI_API_KEY=你的-openrouter-api-key

# 生产环境
ENV=production

# 其他配置根据需要调整
```

### 2.3 启动服务

```bash
cd docker
docker compose -f docker-compose.prod.yml up -d --build
```

首次构建约需 3-5 分钟。

### 2.4 验证部署

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx

# 测试健康接口
curl http://localhost/health
```

---

## 3. 域名配置

### 3.1 DNS 解析

在你的域名服务商处添加 A 记录：

| 主机记录 | 记录类型 | 记录值 | TTL |
|---------|---------|-------|-----|
| trades | A | <你的服务器IP> | 600 |

### 3.2 验证访问

等待 DNS 生效后，浏览器访问：

```
http://trades.zzy88.com
```

---

## 4. 可选：配置 HTTPS（推荐）

### 4.1 使用 Certbot 申请 SSL 证书

```bash
# 安装 Certbot
sudo apt install -y certbot

# 申请证书（ standalone 模式，需先停止 nginx）
docker compose -f docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d trades.zzy88.com

# 证书位置：/etc/letsencrypt/live/trades.zzy88.com/
```

### 4.2 更新 Nginx 配置支持 HTTPS

创建 `docker/nginx.ssl.conf`：

```nginx
server {
    listen 80;
    server_name trades.zzy88.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name trades.zzy88.com;

    ssl_certificate /etc/letsencrypt/live/trades.zzy88.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trades.zzy88.com/privkey.pem;

    client_max_body_size 50M;

    gzip on;
    gzip_types text/css application/javascript application/json text/html;
    gzip_min_length 256;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://backend:8000;
    }

    location ~* \.(js|css)$ {
        root /usr/share/nginx/html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 4.3 更新 docker-compose 挂载证书

修改 `docker-compose.prod.yml` 中 nginx 服务的 volumes：

```yaml
nginx:
  volumes:
    - ./nginx.ssl.conf:/etc/nginx/conf.d/default.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  ports:
    - "80:80"
    - "443:443"
```

### 4.4 重启服务

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## 5. 常用运维命令

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 停止服务
docker compose -f docker-compose.prod.yml down

# 完全重置（删除数据卷）
docker compose -f docker-compose.prod.yml down -v

# 进入容器
docker compose -f docker-compose.prod.yml exec backend bash

# 数据库迁移（如需要）
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# 备份数据库
docker compose -f docker-compose.prod.yml exec backend tar -czvf /tmp/db_backup.tar.gz /app/data
docker cp <container_id>:/tmp/db_backup.tar.gz ./
```

---

## 6. 更新部署

```bash
cd ~/intent-money

# 拉取最新代码（如使用 git）
git pull

# 重新构建并启动
cd docker
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 7. 故障排查

### 容器启动失败

```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs backend

# 检查端口占用
sudo lsof -i :80
```

### 前端空白页

1. 打开浏览器开发者工具查看 Console 错误
2. 检查 Nginx 配置是否正确
3. 确认前端构建成功

### 后端 API 无法访问

```bash
# 测试后端健康接口
curl http://localhost:8000/health

# 检查环境变量是否正确加载
docker compose -f docker-compose.prod.yml exec backend env | grep AI_API_KEY
```
