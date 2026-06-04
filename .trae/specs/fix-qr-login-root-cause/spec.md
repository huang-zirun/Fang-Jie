# 扫码登录全链路根因修复 Spec

## Why

小红书和抖音扫码登录后获取的 Cookie 不完整，导致验证时显示"过期"；CDP 路径下扫码登录后前端自动退出登录界面。之前的两次修复（`fix-xhs-login-false-positive`、`xhs-qrcode-login-validation-fix`）只修补了 Playwright 路径，CDP 路径和验证链路仍存在架构级缺陷。本次修复拒绝 ad hoc patch，从根因出发统一修复。

## What Changes

- **BREAKING** 统一 CDP 和 Playwright 两条路径的登录 URL、登录检测逻辑、session 生命周期管理
- **BREAKING** 重写抖音 Cookie 验证逻辑，支持 storage_state 格式
- 修复 CDP session 清理导致的竞态条件（confirmed 状态丢失）
- 补全 CDP `get_storage_state()` 缺失的 localStorage 数据
- 统一 cookie 验证入口，消除 `accounts.py` 和 `cookie_lifecycle.py` 的重复验证逻辑

## Impact

- Affected specs: 扫码登录、Cookie 验证、账号管理
- Affected code:
  - `backend/app/services/cdp_qrcode_login.py` — 核心重写
  - `backend/app/services/qrcode_login.py` — session 生命周期对齐
  - `backend/app/services/platform_scraper/cdp_browser.py` — 补全 localStorage
  - `backend/app/api/v1/accounts.py` — 验证逻辑统一
  - `backend/app/services/cookie_lifecycle.py` — 验证逻辑统一
  - `backend/app/services/xhs_cookie_validator.py` — 无需改动（已正确）
  - `frontend/src/views/AccountManage.vue` — 无需改动（前端逻辑正确）

## 根因分析

### 根因 1：CDP 路径和 Playwright 路径严重不一致

| 维度 | CDP 路径 (`cdp_qrcode_login.py`) | Playwright 路径 (`qrcode_login.py`) | social-auto-upload 参考 |
|------|------|------|------|
| XHS 登录 URL | `https://www.xiaohongshu.com`（首页） | `https://creator.xiaohongshu.com/login`（登录页） | `https://creator.xiaohongshu.com/login` |
| XHS 登录检测 | 检查登录按钮是否消失 | URL 跳转离开登录页 | URL 跳转 + login-box 不可见 |
| 抖音登录 URL | `https://www.douyin.com` | `https://www.douyin.com` | `https://creator.douyin.com/` |
| 抖音登录检测 | URL 前缀判断 | URL 前缀判断 | URL 跳转到 creator-micro/home + 登录元素不可见 |

**问题**：CDP 路径访问小红书首页而非登录页，首页的登录流程是弹窗模式，极不稳定。之前的修复只改了 Playwright 路径，CDP 路径仍然是旧的错误逻辑。

### 根因 2：CDP session 清理导致 confirmed 状态丢失（"自动退出登录界面"）

**位置**：`cdp_qrcode_login.py` L187-194 和 L240-249

```python
# _poll_cdp_login_status 中：
session.status = "confirmed"
await _cleanup_cdp_session(session.session_id)  # 立即从 _CDP_SESSIONS 中移除

# _cleanup_cdp_session 中：
_CDP_SESSIONS.pop(session_id, None)  # session 消失了
```

**对比 Playwright 路径**：`_cleanup_session()` 只关闭浏览器资源，**不从 `_sessions` 中移除** session，所以前端可以持续轮询到 "confirmed" 状态。

**结果**：CDP 路径下，登录成功后 session 立即被移除。前端下次轮询时 `check_cdp_login_status()` 找不到 session，返回 `{"status": "expired", "message": "登录会话不存在或已过期"}`。前端显示"二维码已过期"，用户看到登录界面自动退出。

### 根因 3：抖音 Cookie 验证不支持 storage_state 格式

**位置**：`accounts.py` L248-254 和 `cookie_lifecycle.py` L58-64

```python
if platform == "douyin":
    headers["Cookie"] = cookie_data  # cookie_data 是 storage_state JSON！
    resp = await client.get(
        "https://www.douyin.com/aweme/v1/web/user/profile/",
        headers=headers,
    )
    return resp.status_code == 200
```

**问题**：
1. 扫码登录保存的是 `storage_state` JSON 格式（`{"cookies": [...], "origins": [...]}`），但验证代码直接把整个 JSON 字符串当作 Cookie 头发送
2. 抖音 API 需要完整的请求头（Referer、Origin 等）和签名参数（x-bd-kms 等），简单的 httpx 请求无法通过验证
3. `status_code == 200` 不代表登录有效，抖音未登录时也会返回 200

**对比 social-auto-upload**：抖音验证使用 Playwright 浏览器加载 storage_state，访问创作者中心，检查是否出现"扫码登录"或"手机号登录"文字。这是唯一可靠的方式。

### 根因 4：CDP `get_storage_state()` 缺失 localStorage

**位置**：`cdp_browser.py` L412-432

```python
async def get_storage_state(self) -> dict:
    cookies = await self.get_cookies()
    ...
    return {"cookies": formatted, "origins": []}  # origins 永远为空！
```

**问题**：小红书和抖音都可能将部分认证数据存储在 localStorage 中。CDP 路径的 `get_storage_state()` 只获取 Cookie，不获取 localStorage，导致保存的 storage_state 不完整。Playwright 的 `context.storage_state()` 会自动包含 localStorage。

### 根因 5：验证逻辑重复且不一致

`accounts.py` 的 `_validate_cookie()` 和 `cookie_lifecycle.py` 的 `_check_platform_login()` 实现了几乎相同的验证逻辑，但维护不同步。任何修改都需要同时改两处，容易遗漏。

## ADDED Requirements

### Requirement: 统一登录 URL 配置

系统 SHALL 在 CDP 和 Playwright 两条路径中使用相同的登录 URL：
- XHS: `https://creator.xiaohongshu.com/login`
- 抖音: `https://creator.douyin.com/`

#### Scenario: CDP 路径访问小红书登录页
- **WHEN** 用户通过 CDP 路径启动小红书扫码登录
- **THEN** 系统导航到 `https://creator.xiaohongshu.com/login`
- **AND** 页面显示独立的登录界面（非首页弹窗）

#### Scenario: CDP 路径访问抖音登录页
- **WHEN** 用户通过 CDP 路径启动抖音扫码登录
- **THEN** 系统导航到 `https://creator.douyin.com/`
- **AND** 页面显示抖音创作者中心登录界面

### Requirement: 统一登录检测逻辑

系统 SHALL 在 CDP 和 Playwright 路径中使用相同的登录检测策略：
- XHS: 页面 URL 跳转离开 `https://creator.xiaohongshu.com/login` 且 login-box 不可见
- 抖音: 页面 URL 跳转到 `https://creator.douyin.com/creator-micro/home` 且登录元素不可见

#### Scenario: XHS 登录成功检测
- **WHEN** 用户扫码确认登录
- **THEN** 页面 URL 不再以 `https://creator.xiaohongshu.com/login` 开头
- **AND** 页面上不存在可见的 `div[class*='login-box']` 元素

#### Scenario: 抖音登录成功检测
- **WHEN** 用户扫码确认登录
- **THEN** 页面 URL 以 `https://creator.douyin.com/creator-micro/home` 开头
- **AND** 页面上不存在可见的"扫码登录"或"手机号登录"文字

### Requirement: CDP session 生命周期与 Playwright 对齐

系统 SHALL 在 CDP 路径中，登录确认后不立即移除 session，保留一段时间供前端轮询。

#### Scenario: 登录成功后前端轮询
- **WHEN** CDP 扫码登录成功
- **AND** session 状态设为 "confirmed"
- **THEN** session 在 `_CDP_SESSIONS` 中保留至少 30 秒
- **AND** 前端轮询能获取到 "confirmed" 状态

#### Scenario: 登录成功后自动清理
- **WHEN** CDP session 状态为 "confirmed" 超过 30 秒
- **THEN** 系统自动清理该 session

### Requirement: CDP storage_state 包含 localStorage

系统 SHALL 在 CDP 路径获取 storage_state 时，同时获取 localStorage 数据。

#### Scenario: 获取完整 storage_state
- **WHEN** CDP 登录检测成功
- **THEN** `get_storage_state()` 返回包含 cookies 和 localStorage 的完整 storage_state
- **AND** origins 列表包含当前页面的 localStorage 数据

### Requirement: 抖音 Cookie 验证使用浏览器方式

系统 SHALL 使用 Playwright 浏览器验证抖音 Cookie，与小红书验证方式一致。

#### Scenario: 抖音 storage_state 格式验证
- **WHEN** 用户点击抖音账号的"验证"按钮
- **AND** 存储的 Cookie 为 storage_state JSON 格式
- **THEN** 系统使用 Playwright 加载 storage_state
- **AND** 访问抖音创作者中心
- **AND** 检查是否出现"扫码登录"或"手机号登录"文字
- **AND** 未出现则返回"有效"

#### Scenario: 抖音 cookie_string 格式验证
- **WHEN** 用户点击抖音账号的"验证"按钮
- **AND** 存储的 Cookie 为 cookie 字符串格式
- **THEN** 系统解析 cookie 字符串为 Playwright cookie 格式
- **AND** 使用 Playwright 加载 cookie
- **AND** 访问抖音创作者中心验证

### Requirement: 统一验证入口

系统 SHALL 将 Cookie 验证逻辑统一到单一模块，`accounts.py` 和 `cookie_lifecycle.py` 共用同一验证函数。

#### Scenario: API 端点验证
- **WHEN** 前端调用 `POST /accounts/{platform}/validate`
- **THEN** 后端调用统一的 `validate_platform_cookie(platform, cookie_data)` 函数

#### Scenario: 定时批量验证
- **WHEN** 定时任务执行 Cookie 生命周期检查
- **THEN** 后端调用同一 `validate_platform_cookie(platform, cookie_data)` 函数

## MODIFIED Requirements

### Requirement: CDP 扫码登录流程

修改 `cdp_qrcode_login.py` 的完整流程：

1. 访问 `https://creator.xiaohongshu.com/login`（XHS）或 `https://creator.douyin.com/`（抖音）
2. 等待二维码元素出现，提取 base64 原图或截图返回前端
3. 轮询检测登录状态（URL 跳转 + 登录元素不可见）
4. 登录成功后，获取完整 storage_state（含 localStorage）
5. 保留 session 30 秒供前端轮询

### Requirement: CDP 浏览器 storage_state 获取

修改 `cdp_browser.py` 的 `get_storage_state()` 方法：

1. 获取所有 Cookie（已有）
2. 通过 `Runtime.evaluate` 获取当前页面的 localStorage
3. 将 localStorage 数据格式化为 Playwright storage_state 的 origins 格式
4. 返回完整的 `{"cookies": [...], "origins": [...]}`

### Requirement: 抖音 Cookie 验证

修改 `accounts.py` 和 `cookie_lifecycle.py` 中的抖音验证逻辑：

1. 检测 cookie_data 格式（storage_state JSON 或 cookie_string）
2. 使用 Playwright 浏览器加载 cookie
3. 访问 `https://creator.douyin.com/creator-micro/content/upload`
4. 检查是否出现"扫码登录"或"手机号登录"文字
5. 未出现则返回 True（有效），出现则返回 False（过期）

## REMOVED Requirements

### Requirement: 基于 httpx 的抖音 Cookie 验证

**Reason**: 抖音 API 需要签名参数和完整请求头，httpx 直接请求无法可靠验证。改用 Playwright 浏览器验证。
**Migration**: 删除 `accounts.py` 和 `cookie_lifecycle.py` 中的 httpx 抖音验证代码，改用 Playwright 浏览器验证。

### Requirement: CDP 路径基于登录按钮消失的 XHS 登录检测

**Reason**: 首页登录按钮的 CSS 选择器不稳定，且首页弹窗模式本身不可靠。改用创作者中心登录页 + URL 跳转检测。
**Migration**: 删除 `_check_login_done()` 中基于登录按钮的检测逻辑，统一使用 URL 跳转 + 登录元素不可见的检测方式。
