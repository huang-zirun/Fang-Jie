# 多账号管理与 Per-User Cookie 抓取 Spec

## Why

项目部署到 Ubuntu 无头服务器后，小红书/抖音的登录 Cookie 无法通过 CDP 连接已登录 Chrome 获取（服务器无桌面）。用户需要多账号管理机制：每个用户绑定自己的平台账号，使用自己的 Cookie 抓取实时爆款数据，实现数据隔离和个性化引流。

## What Changes

- 新增 `user_platform_accounts` 数据模型，存储用户绑定的平台账号及加密 Cookie
- 新增 Cookie 加密存储服务（AES-256-GCM），替代当前文件明文存储
- 新增账号绑定 API（Cookie 手动导入 + 验证、QR 码登录中转）
- 新增 Per-User Cookie 抓取架构：为每个用户创建注入其 Cookie 的 Scraper 实例
- 新增前端账号管理页面：绑定/解绑平台账号、查看 Cookie 状态、手动导入 Cookie
- 新增 Cookie 生命周期管理：自动验证、过期提醒、状态追踪
- 修改现有 CDP 抓取逻辑，支持按用户 Cookie 切换抓取身份
- **BREAKING**: `cookie_manager.py` 从文件存储迁移到数据库加密存储
- **BREAKING**: 爬虫 API 需要用户认证，按用户身份抓取数据

## Impact

- Affected specs: intent-money-full（数据抓取架构变更）、cloud-deployment（CDP 依赖降低）
- Affected code:
  - Backend: `app/models/`（新增 UserPlatformAccount）、`app/services/cookie_manager.py`（重写为加密存储）、`app/services/platform_scraper/`（Per-User Cookie 注入）、`app/api/v1/scraper.py`（需认证）、`app/api/v1/`（新增 accounts 路由）、`app/config.py`（新增加密密钥配置）
  - Frontend: 新增 `views/AccountManage.vue`、修改 `router/index.ts`、修改 `stores/`、修改 `api/`
  - DB: 新增 `user_platform_accounts` 表，Alembic 迁移

## ADDED Requirements

### Requirement: 用户平台账号绑定

系统 SHALL 允许每个用户绑定自己的小红书/抖音平台账号，每个用户每个平台可绑定一个账号。绑定方式包括 Cookie 手动导入和 QR 码扫码登录。

#### Scenario: 用户手动导入 Cookie 绑定账号
- **WHEN** 用户在前端账号管理页面选择"手动导入 Cookie"，选择平台（小红书/抖音），粘贴 Cookie 字符串
- **THEN** 系统验证 Cookie 有效性，验证通过后加密存储，绑定状态变为 `bound`，Cookie 状态变为 `active`

#### Scenario: 用户通过 QR 码扫码绑定账号
- **WHEN** 用户在前端选择"扫码登录"，选择平台
- **THEN** 系统启动 Playwright headless 浏览器打开平台登录页，截取 QR 码图片返回前端；用户手机扫码后，系统检测登录成功，提取 Cookie 加密存储

#### Scenario: Cookie 验证失败
- **WHEN** 用户导入的 Cookie 无效或已过期
- **THEN** 系统返回明确的错误信息"Cookie 无效或已过期，请重新获取"，绑定状态不变

#### Scenario: 用户解绑账号
- **WHEN** 用户点击"解绑"按钮
- **THEN** 系统删除该平台账号的加密 Cookie 和绑定记录，相关抓取功能不可用

### Requirement: Cookie 加密存储

系统 SHALL 使用 AES-256-GCM 加密存储所有平台 Cookie，每条 Cookie 使用独立 IV，以 user_id 作为 AAD（附加认证数据）防止跨用户替换。主密钥通过环境变量 `COOKIE_ENCRYPTION_KEY` 配置。

#### Scenario: Cookie 加密存储
- **WHEN** 用户绑定平台账号成功
- **THEN** Cookie 使用 AES-256-GCM 加密后存入 `user_platform_accounts` 表，IV 独立存储，解密时验证 AAD

#### Scenario: Cookie 解密使用
- **WHEN** 系统需要使用某用户的 Cookie 进行抓取
- **THEN** 从数据库读取加密 Cookie 和 IV，使用主密钥 + user_id AAD 解密，仅在请求作用域内存在

#### Scenario: 主密钥未配置
- **WHEN** `COOKIE_ENCRYPTION_KEY` 环境变量未设置
- **THEN** 后端启动时发出警告日志，开发模式下使用固定密钥（仅限开发），生产模式拒绝启动

### Requirement: Per-User Cookie 抓取

系统 SHALL 支持按用户身份抓取平台数据：使用每个用户自己的 Cookie 创建独立的 Scraper 实例，实现数据隔离。当用户未绑定某平台账号时，该平台抓取功能不可用。

#### Scenario: 用户请求抓取数据
- **WHEN** 已登录用户请求抓取小红书/抖音爆款数据
- **THEN** 系统从数据库获取该用户绑定的平台 Cookie，解密后注入 Scraper，使用用户身份抓取数据

#### Scenario: 用户未绑定平台账号
- **WHEN** 用户请求抓取某平台数据但未绑定该平台账号
- **THEN** 系统返回 403 错误"请先绑定{平台}账号"，引导用户前往账号管理页面

#### Scenario: 用户 Cookie 已过期
- **WHEN** 用户请求抓取数据但 Cookie 已过期
- **THEN** 系统自动将 Cookie 状态标记为 `expired`，返回 403 错误"Cookie 已过期，请重新绑定账号"

#### Scenario: CDP 模式降级兼容
- **WHEN** 管理员未配置 Per-User 模式（`PER_USER_SCRAPING=false`）
- **THEN** 系统回退到原有 CDP 共享实例模式，使用全局 Chrome 抓取数据

### Requirement: Cookie 生命周期管理

系统 SHALL 管理 Cookie 的完整生命周期：验证、过期检测、状态追踪。Cookie 状态包括 `pending`（待验证）、`active`（有效）、`expired`（已过期）、`invalid`（无效）。

#### Scenario: 定时验证 Cookie 有效性
- **WHEN** 系统定时任务触发（每日一次）
- **THEN** 对所有 `active` 状态的 Cookie 执行有效性验证，失效的标记为 `expired`

#### Scenario: Cookie 即将过期提醒
- **WHEN** Cookie 距离过期不足 2 天
- **THEN** 系统在前端显示"Cookie 即将过期"提醒，引导用户重新绑定

#### Scenario: 抓取时自动检测 Cookie 失效
- **WHEN** 使用用户 Cookie 抓取数据时收到 401 响应
- **THEN** 系统自动将该 Cookie 标记为 `expired`，下次请求时提示用户重新绑定

### Requirement: 前端账号管理页面

系统 SHALL 提供账号管理页面，用户可查看已绑定的平台账号列表、Cookie 状态、绑定时间，支持手动导入 Cookie、扫码登录、解绑操作。

#### Scenario: 查看已绑定账号
- **WHEN** 用户进入账号管理页面
- **THEN** 显示已绑定的平台账号卡片，每个卡片展示平台名称、昵称、Cookie 状态（正常/即将过期/已过期/未绑定）、最后验证时间

#### Scenario: 手动导入 Cookie
- **WHEN** 用户点击"导入 Cookie"按钮
- **THEN** 弹出对话框，用户选择平台、粘贴 Cookie 字符串，系统验证后绑定

#### Scenario: 扫码登录
- **WHEN** 用户点击"扫码登录"按钮
- **THEN** 弹出对话框展示 QR 码图片，用户用手机 APP 扫码，系统自动检测登录成功

### Requirement: 抓取请求限速

系统 SHALL 对每个用户的平台抓取请求实施限速，防止触发平台反爬机制。小红书 10 次/分钟，抖音 15 次/分钟。

#### Scenario: 用户请求频率超限
- **WHEN** 用户在 1 分钟内对小红书发起超过 10 次抓取请求
- **THEN** 系统返回 429 错误"请求过于频繁，请稍后再试"

## MODIFIED Requirements

### Requirement: 数据抓取架构

原 CDP 模式使用单一共享 Chrome 实例抓取数据。修改为支持两种模式：
- **Per-User 模式**（默认）：使用用户自己的 Cookie 通过 httpx 异步请求抓取，数据隔离
- **CDP 共享模式**（降级）：当 `PER_USER_SCRAPING=false` 时回退到原有 CDP 共享实例

### Requirement: 爬虫 API 认证

原爬虫 API 无需认证即可调用。修改为需要用户认证（JWT），按用户身份抓取数据。管理员可配置是否保留无需认证的全局抓取接口。

### Requirement: Cookie 存储

原 `cookie_manager.py` 使用文件系统明文存储 Cookie。修改为使用数据库 + AES-256-GCM 加密存储，通过 `CookieVault` 服务统一管理加密/解密。

## REMOVED Requirements

### Requirement: 环境变量静态 Cookie 配置
**Reason**: Cookie 改为按用户动态管理，不再使用全局环境变量 `DOUYIN_COOKIE` / `XHS_COOKIE`
**Migration**: 保留环境变量作为 CDP 共享模式的降级配置，Per-User 模式下不使用

### Requirement: Cookie 文件存储
**Reason**: 文件明文存储不安全，迁移到数据库加密存储
**Migration**: 现有 `backend/cookies/` 目录下的 Cookie 文件在迁移后可删除，新数据存入 `user_platform_accounts` 表
