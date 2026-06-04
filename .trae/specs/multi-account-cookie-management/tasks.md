# Tasks

- [x] Task 1: 新增 UserPlatformAccount 数据模型与 Alembic 迁移
  - [x] SubTask 1.1: 创建 `app/models/user_platform_account.py`，定义 UserPlatformAccount 模型
  - [x] SubTask 1.2: 在 `app/models/__init__.py` 中注册新模型
  - [x] SubTask 1.3: 在 User 模型中添加 `platform_accounts` relationship
  - [x] SubTask 1.4: 创建 Alembic 迁移脚本（`render_as_batch=True` 兼容 SQLite）
  - [x] SubTask 1.5: 创建 Pydantic Schema（`app/schemas/account.py`）

- [x] Task 2: 实现 CookieVault 加密存储服务
  - [x] SubTask 2.1: 创建 `app/services/cookie_vault.py`，实现 AES-256-GCM 加密/解密
  - [x] SubTask 2.2: 在 `app/config.py` 中添加 `COOKIE_ENCRYPTION_KEY` 和 `PER_USER_SCRAPING` 配置项
  - [x] SubTask 2.3: 重写 `app/services/cookie_manager.py`，从文件存储迁移到数据库加密存储

- [x] Task 3: 实现账号绑定 API
  - [x] SubTask 3.1: 创建 `app/api/v1/accounts.py`，实现 4 个端点
  - [x] SubTask 3.2: 在 `app/api/v1/router.py` 中注册 accounts 路由
  - [x] SubTask 3.3: 实现平台 Cookie 验证逻辑

- [x] Task 4: 实现 QR 码扫码登录 API
  - [x] SubTask 4.1: 创建 `app/services/qrcode_login.py`
  - [x] SubTask 4.2: 实现 QR 码登录状态轮询端点
  - [x] SubTask 4.3: 实现登录成功后 Cookie 自动提取和加密存储
  - [x] SubTask 4.4: 在 `pyproject.toml` 中添加 `playwright` 依赖

- [x] Task 5: 实现 Per-User Cookie 抓取架构
  - [x] SubTask 5.1: 创建 `app/services/per_user_scraper.py`
  - [x] SubTask 5.2: 修改 `app/api/v1/scraper.py`，添加用户认证依赖
  - [x] SubTask 5.3: 修改 `app/services/market_service.py`，支持按用户 Cookie 抓取
  - [x] SubTask 5.4: 实现抓取请求限速（小红书 10rpm，抖音 15rpm）

- [x] Task 6: 实现 Cookie 生命周期管理
  - [x] SubTask 6.1: 创建 `app/services/cookie_lifecycle.py`
  - [x] SubTask 6.2: 在 `app/main.py` 中注册定时任务
  - [x] SubTask 6.3: 实现抓取时自动检测 Cookie 失效

- [x] Task 7: 前端账号管理页面
  - [x] SubTask 7.1: 创建 `frontend/src/views/AccountManage.vue`
  - [x] SubTask 7.2: 实现手动导入 Cookie 对话框
  - [x] SubTask 7.3: 实现扫码登录对话框
  - [x] SubTask 7.4: 实现解绑操作
  - [x] SubTask 7.5: 在 `frontend/src/router/index.ts` 中添加路由
  - [x] SubTask 7.6: 在 `frontend/src/api/` 中添加 API 调用
  - [x] SubTask 7.7: 在导航栏中添加账号管理入口

- [x] Task 8: 集成测试与验证
  - [x] SubTask 8.1: 编写 CookieVault 加密/解密单元测试（5 个测试全部通过）
  - [x] SubTask 8.2: 编写账号绑定 API 集成测试（4 个测试全部通过）
  - [x] SubTask 8.3: 编写限速器单元测试（4 个测试全部通过）
  - [x] SubTask 8.4: 手动端到端测试需用户在运行环境中验证

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1, Task 2]
- [Task 4] depends on [Task 1, Task 2]
- [Task 5] depends on [Task 1, Task 2, Task 3]
- [Task 6] depends on [Task 1, Task 2]
- [Task 7] depends on [Task 3, Task 4]
- [Task 8] depends on [Task 5, Task 6, Task 7]
