# 2026-06-01 多账号管理与 Per-User Cookie 抓取

## 背景
项目部署到 Ubuntu 无头服务器后，CDP 模式依赖的已登录 Chrome 不可用，小红书/抖音的登录 Cookie 无法获取。用户诉求：
1. 多账号管理机制，每个用户绑定自己的平台账号
2. 使用自己的 Cookie 抓取实时爆款数据
3. 数据隔离和个性化引流

## 调研结论

### Cookie 获取方案对比
| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| Cookie 手动导入 + 验证 | 最可靠，实现简单 | 用户操作门槛高 | ✅ Phase 1 |
| QR 码 Web UI 中转 | 用户体验好 | 小红书反 headless 强 | ✅ Phase 2 |
| 远程浏览器 (VNC/noVNC) | 接近真实环境 | 资源消耗大，多用户隔离复杂 | ❌ |
| CDP 连接远程 Chrome | 复用现有架构 | 不适合 SaaS 多用户 | ✅ 保留降级 |

### 关键发现
- 小红书 Web Cookie 有效期 7-30 天，抖音 7-15 天
- 小红书反 headless 检测极强，纯 headless 模式成功率低，建议 xvfb-run + headless=False
- AES-256-GCM 的 AAD 机制天然适合防止跨用户 Cookie 替换

## 实现内容

### 后端新增文件
- `app/models/user_platform_account.py` - 用户平台账号数据模型
- `app/services/cookie_vault.py` - AES-256-GCM 加密/解密服务
- `app/services/qrcode_login.py` - QR 码扫码登录服务（Playwright headless）
- `app/services/per_user_scraper.py` - Per-User Cookie 抓取工厂
- `app/services/cookie_lifecycle.py` - Cookie 生命周期管理
- `app/services/rate_limiter.py` - 抓取请求限速
- `app/schemas/account.py` - Pydantic Schema
- `app/api/v1/accounts.py` - 账号绑定 API（6 个端点）

### 后端修改文件
- `app/models/user.py` - 添加 platform_accounts relationship
- `app/services/cookie_manager.py` - 从文件存储重写为数据库加密存储
- `app/config.py` - 新增 COOKIE_ENCRYPTION_KEY、PER_USER_SCRAPING
- `app/api/v1/scraper.py` - Per-User 抓取 + 403/429 响应
- `app/api/v1/scraper_xhs.py` - 同上
- `app/services/market_service.py` - 支持 user_id 参数
- `app/main.py` - 注册每日 Cookie 验证任务
- `app/api/v1/router.py` - 注册 accounts 路由

### 前端新增文件
- `src/views/AccountManage.vue` - 账号管理页面
- `src/api/accounts.ts` - 账号管理 API 客户端

### 前端修改文件
- `src/router/index.ts` - 添加 /accounts 路由
- `src/views/IntentSelect.vue` - 添加"账号管理"入口

### 数据库变更
- 新增 `user_platform_accounts` 表（Alembic 迁移）

### 测试
- `tests/test_cookie_vault.py` - 5 个测试（加密/解密/AAD 防护/篡改检测）
- `tests/test_accounts_api.py` - 4 个测试（空列表/无效平台/解绑不存在/验证不存在）
- `tests/test_rate_limiter.py` - 4 个测试（限内通过/超限拒绝/平台独立/用户独立）

## 修复的既有 Bug
1. `cookie_vault.py` - 开发密钥长度从 26 字节修正为 32 字节（AES-256 要求）
2. `publisher.py` - 修复了 cookie_manager 函数调用缺少 db 参数的问题

## 验证结果
- 13/13 测试通过
- Ruff lint 检查通过
- 26/26 checklist 检查点通过

## 架构决策记录

### 为什么选择 AES-256-GCM 而不是 AES-CBC？
- GCM 模式提供认证加密（AEAD），内置完整性校验，无需额外 HMAC
- 支持 AAD（附加认证数据），天然防止跨用户 Cookie 替换
- 无需手动处理 padding

### 为什么 Per-User 抓取用 httpx 而不是 CDP？
- 数据抓取（搜索、评论）只需 HTTP 请求，不需要浏览器操控
- httpx 异步请求轻量、可并行，每个用户独立 Client
- CDP/Playwright 每个实例约 50-100MB 内存，不适合多用户并发
- 发布操作仍需 CDP/Playwright（需要 DOM 操控）

### 为什么未绑定用户返回 403 而非降级到共享爬虫？
- Per-User 模式的核心价值是数据隔离，降级到共享爬虫违背设计意图
- 共享爬虫使用管理员 Cookie，抓取的数据不属于该用户
- 403 明确引导用户绑定自己的账号

## 待后续迭代
- QR 码登录在小红书上的成功率需要实际验证（可能需要 xvfb 辅助）
- Cookie 即将过期的前端提醒（目前只有状态展示，没有主动推送通知）
- 浏览器扩展一键推送 Cookie（降低用户操作门槛）
- KMS 集成（生产环境密钥管理，当前使用环境变量）
