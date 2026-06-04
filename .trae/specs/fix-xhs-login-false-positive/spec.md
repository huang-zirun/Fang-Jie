# 小红书扫码登录误判"已登录"问题修复 Spec

## Why

用户清除小红书 Cookie 后，在意图变现系统点击扫码登录，**并未实际扫码**，系统却显示"已经登录"。点击验证又显示"过期"。这说明登录检测逻辑存在根本性缺陷——**误将未登录状态判定为已登录**。

## What Changes

- **BREAKING** 重写 `_is_logged_in()` 登录检测逻辑，从"检测 Cookie 存在"改为"检测页面跳转离开登录页"
- 重写 `_poll_login_status()` 轮询逻辑，使用页面 URL 变化而非 Cookie 检测来判断登录成功
- 修改 `start_qr_login()` 访问小红书创作者登录页而非首页
- 修改登录成功后的 Cookie 保存方式，使用 Playwright `storage_state` 而非拼接 Cookie 字符串

## Impact

- Affected specs: 账号管理、扫码登录、Cookie 验证
- Affected code:
  - `backend/app/services/qrcode_login.py` - 核心重写
  - `backend/app/api/v1/accounts.py` - 适配 storage_state 格式
  - `backend/app/services/xhs_cookie_validator.py` - 适配 storage_state 格式

## 根因分析

### 问题 1：登录检测逻辑错误

**位置**: `qrcode_login.py` 第 140-149 行

```python
def _is_logged_in(platform: str, cookies: list[dict]) -> bool:
    cookie_names = {c["name"] for c in cookies}
    if platform == "xhs":
        return "web_session" in cookie_names or "a1" in cookie_names
```

**问题**：小红书首页在未登录状态下也会设置 `a1` Cookie（这是设备标识 Cookie，不是登录态 Cookie）。因此即使用户没有扫码登录，`_is_logged_in()` 也会返回 `True`，因为 `a1` 在访问首页时就已经被设置了。

### 问题 2：访问了错误的 URL

**位置**: `qrcode_login.py` 第 34-36 行

```python
PLATFORM_LOGIN_URLS = {
    "xhs": "https://www.xiaohongshu.com",  # 首页，不是登录页
}
```

**问题**：访问小红书首页而非登录页。首页在未登录状态下也会设置大量 Cookie（包括 `a1`），导致误判。

### 问题 3：Cookie 保存格式不完整

**位置**: `qrcode_login.py` 第 128 行

```python
cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
```

**问题**：只保存了 name=value，丢失了 domain、path、httpOnly、secure 等属性。小红书的 Cookie 依赖这些属性才能正确工作。

### 正确的实现参考

social-auto-upload 项目在 `xiaohongshu_uploader/main.py` 中的实现：

```python
# 1. 访问登录页（不是首页）
XHS_LOGIN_URL = "https://creator.xiaohongshu.com/login"
await page.goto(XHS_LOGIN_URL)

# 2. 通过页面 URL 变化检测登录成功（不是检测 Cookie）
async def _is_xhs_login_completed(page: Page) -> bool:
    if page.url.startswith(XHS_LOGIN_URL):
        return False  # 还在登录页 = 未登录
    return True  # 跳转离开登录页 = 已登录

# 3. 使用 storage_state 保存完整状态（不是拼接字符串）
await context.storage_state(path=account_file)
```

## ADDED Requirements

### Requirement: 基于页面跳转的登录检测

系统 SHALL 通过检测页面 URL 是否跳转离开登录页来判断登录成功，而非检测 Cookie 存在。

#### Scenario: 用户未扫码，停留在登录页
- **WHEN** Playwright 打开小红书登录页
- **AND** 用户未扫码
- **THEN** 页面 URL 仍为 `https://creator.xiaohongshu.com/login`
- **AND** 系统判定为"未登录"

#### Scenario: 用户扫码登录成功
- **WHEN** 用户使用小红书 APP 扫码并确认登录
- **THEN** 页面 URL 跳转离开 `https://creator.xiaohongshu.com/login`
- **AND** 系统判定为"已登录"

### Requirement: 使用 storage_state 保存登录状态

系统 SHALL 使用 Playwright 的 `storage_state` 格式保存登录状态，包含完整的 Cookie 属性和 localStorage。

#### Scenario: 保存登录状态
- **WHEN** 扫码登录成功
- **THEN** 系统调用 `context.storage_state()` 获取完整状态
- **AND** 将 storage_state JSON 存入数据库

### Requirement: 访问正确的登录 URL

系统 SHALL 访问小红书创作者登录页 `https://creator.xiaohongshu.com/login`，而非首页 `https://www.xiaohongshu.com`。

## MODIFIED Requirements

### Requirement: 扫码登录流程

修改 `qrcode_login.py` 的完整扫码登录流程：

1. 访问 `https://creator.xiaohongshu.com/login`（登录页）
2. 等待二维码元素出现，截图返回前端
3. 轮询检测页面 URL 是否跳转离开登录页
4. 登录成功后，调用 `context.storage_state()` 保存完整状态
5. 将 storage_state JSON 存入数据库

### Requirement: Cookie 验证

修改 `xhs_cookie_validator.py`，支持 storage_state 格式的验证：

1. 从数据库读取 storage_state JSON
2. 使用 `browser.new_context(storage_state=...)` 加载状态
3. 访问创作者中心
4. 检查是否被重定向到登录页

### Requirement: 数据库存储格式

修改 `user_platform_accounts` 表的 Cookie 存储：

- `encrypted_cookie` 字段存储 `storage_state` JSON（而非 `name=value; name=value` 字符串）
- storage_state 格式：`{"cookies": [...], "origins": [...]}`

## REMOVED Requirements

### Requirement: 基于 Cookie 名称的登录检测

**Reason**: `a1` Cookie 在未登录时也会被设置，导致误判。应改为基于页面 URL 跳转检测。
**Migration**: 删除 `_is_logged_in()` 函数，改用页面 URL 检测。

### Requirement: Cookie 字符串拼接存储

**Reason**: 丢失 Cookie 属性（domain、path、httpOnly、secure），导致验证失败。
**Migration**: 改用 Playwright `storage_state` 格式存储。
