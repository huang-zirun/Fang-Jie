# Tasks

- [x] Task 1: 创建 Backend Dockerfile
  - [x] SubTask 1.1: 编写基于 python:3.11-slim 的 Dockerfile，使用 uv 安装依赖
  - [x] SubTask 1.2: 配置非 root 用户运行、健康检查、环境变量
  - [x] SubTask 1.3: 验证 `docker build` 成功

- [x] Task 2: 创建 Frontend Dockerfile（多阶段构建）
  - [x] SubTask 2.1: 第一阶段：Node 构建 Vue 静态资源
  - [x] SubTask 2.2: 第二阶段：Nginx 托管构建产物
  - [x] SubTask 2.3: 验证 `docker build` 成功

- [x] Task 3: 重构 docker-compose.yml 为生产模式
  - [x] SubTask 3.1: 去掉开发用的 volume mounts 和 --reload
  - [x] SubTask 3.2: 合并 frontend 和 nginx 为单一服务（Nginx 托管前端 + 代理后端）
  - [x] SubTask 3.3: 添加 restart 策略、环境变量引用、.env 文件支持
  - [x] SubTask 3.4: 验证 `docker compose up` 所有服务正常启动

- [x] Task 4: 增强 nginx.conf 为生产级配置
  - [x] SubTask 4.1: 添加前端静态资源托管（root 指令）
  - [x] SubTask 4.2: 添加 API 反向代理、WebSocket/SSE 支持
  - [x] SubTask 4.3: 添加 Gzip 压缩、静态资源缓存、安全头部
  - [x] SubTask 4.4: 验证前端页面和 API 请求均正常

- [x] Task 5: 修改后端 CDP 配置支持远程连接
  - [x] SubTask 5.1: 确认 CDP_DEBUG_HOST/CDP_DEBUG_PORT 环境变量已可配置远程地址
  - [x] SubTask 5.2: 添加 CDP 连接健康检查 API 端点（返回 CDP 可用状态）
  - [x] SubTask 5.3: 添加 CDP_DEBUG_SCHEME 支持 HTTPS（cloudflared 穿透）

- [x] Task 6: 创建本地 Chrome 启动脚本
  - [x] SubTask 6.1: 编写 Windows PowerShell 脚本 `scripts/start-chrome.ps1`
  - [x] SubTask 6.2: 编写 macOS/Linux Shell 脚本 `scripts/start-chrome.sh`
  - [x] SubTask 6.3: 验证脚本启动 Chrome 后 CDP 端口可访问

- [x] Task 7: 编写内网穿透配置指南和示例
  - [x] SubTask 7.1: 编写 frp 配置示例（frpc.ini）和步骤说明
  - [x] SubTask 7.2: 编写 cloudflared 配置示例和步骤说明
  - [x] SubTask 7.3: 将指南写入部署文档

- [x] Task 8: 编写部署文档
  - [x] SubTask 8.1: 服务器环境准备（Docker 安装、防火墙配置）
  - [x] SubTask 8.2: 环境变量说明（.env 文件模板）
  - [x] SubTask 8.3: 一键部署步骤
  - [x] SubTask 8.4: CDP 连接配置和验证步骤
  - [x] SubTask 8.5: 常见问题排查

# Task Dependencies
- [Task 2] depends on [Task 4]（Frontend Dockerfile 的 Nginx 配置需要与 nginx.conf 一致）
- [Task 3] depends on [Task 1, Task 2]（docker-compose.yml 引用 Dockerfile）
- [Task 5] depends on [Task 3]（需要容器运行后验证 CDP 远程连接）
- [Task 8] depends on [Task 3, Task 5, Task 6, Task 7]（文档汇总所有配置）
