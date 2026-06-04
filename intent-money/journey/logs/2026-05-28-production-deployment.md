# 2026-05-28 生产部署

## 概述
将 Intent Money OS 部署到服务器 `trades.zzy88.com`，端口 9090。

## 部署配置

### 服务器信息
- 域名：`trades.zzy88.com`
- 端口：9090（通过服务器 Nginx 反向代理到 80）
- 项目路径：`/srv/Fang-Jie/intent-money`

### 架构
```
用户浏览器
    ↓
http://trades.zzy88.com:80
    ↓
服务器 Nginx（反向代理）
    ↓
http://127.0.0.1:9090
    ↓
Docker Nginx 容器
    ↓
Docker Backend 容器（FastAPI :8000）
    ↓
SQLite 数据库（/app/data/intent_money.db）
```

## 遇到的问题及解决方案

### 问题 1：Alembic 迁移冲突（Multiple head revisions）
- **原因**：多个迁移文件有相同的 revision ID 或依赖关系混乱
- **解决**：删除所有旧迁移文件，创建单一完整的初始迁移 `000000000000_initial_migration.py`

### 问题 2：AI_API_KEY 环境变量未传递
- **原因**：docker-compose 中 `environment` 的 `${AI_API_KEY}` 从 shell 环境读取，而非 `.env` 文件
- **解决**：简化 docker-compose 配置，让 `env_file` 完全接管环境变量加载

### 问题 3：数据库表不存在
- **原因**：初始迁移不完整，缺少基础表定义
- **解决**：创建包含所有 14 个表的完整初始迁移

### 问题 4：数据库文件无法打开
- **原因**：Docker volume 权限问题，appuser 无法写入 `/app/data`
- **解决**：
  1. Dockerfile 中以 root 启动，先 `chown` 修复权限，再切换到 appuser
  2. SQLite URL 使用四个斜杠表示绝对路径：`sqlite+aiosqlite:////app/data/intent_money.db`

### 问题 5：PYTHONPATH 问题
- **原因**：Alembic 运行时找不到 `app` 模块
- **解决**：在 `entrypoint.sh` 中设置 `export PYTHONPATH=/app`

## 关键文件变更

### 新增文件
- `docker/nginx.prod.conf` - 生产环境 Nginx 配置（域名：trades.zzy88.com）
- `docker/docker-compose.prod.yml` - 生产环境 Docker Compose 配置
- `.github/workflows/deploy.yml` - GitHub Actions 自动部署
- `DEPLOY.md` - 部署文档
- `backend/alembic/versions/000000000000_initial_migration.py` - 完整初始迁移

### 修改文件
- `backend/Dockerfile` - 添加数据目录创建和权限修复
- `backend/entrypoint.sh` - 添加 PYTHONPATH 和数据目录创建
- `backend/alembic/versions/*.py` - 删除所有旧迁移文件

## 验证命令

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 测试健康接口
curl http://trades.zzy88.com/health

# 测试 API
curl http://trades.zzy88.com/api/v1/auth/anonymous

# 浏览器访问
http://trades.zzy88.com
```

## 后续工作
- [ ] 配置 HTTPS（Let's Encrypt）
- [ ] 配置 CDP 连接（如需自动化发布）
- [ ] 设置数据库备份
