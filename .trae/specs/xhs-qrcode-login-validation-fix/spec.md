# 小红书扫码登录验证过期问题修复 Spec

## Why

用户反馈：小红书平台点击扫码登录，登录成功后，点击验证，显示验证过期。需要查清这个链路失败的原因并修复。

## What Changes

- 修复 `_validate_cookie()` 函数，添加必要的请求头（Referer、Origin 等）
- 增强 `_is_logged_in()` 登录检测逻辑，检查更多必要 cookie
- 优化 cookie 存储格式，确保完整性
- 添加调试日志便于问题排查

## Impact

- Affected specs: 账号管理、Cookie 验证
- Affected code: 
  - `backend/app/services/qrcode_login.py`
  - `backend/app/api/v1/accounts.py`
  - `backend/app/services/cookie_lifecycle.py`

## 问题根因分析

### 链路流程

```
用户点击"扫码登录" 
  → 前端调用 POST /accounts/xhs/qrcode
  → 后端启动 Playwright 浏览器访问小红书
  → 截取二维码图片返回前端
  → 后端轮询检测登录状态 (_poll_login_status)
  → 检测到 web_session 或 a1 cookie 存在
  → 保存所有 cookie 到数据库
  → 前端显示"登录成功"

用户点击"验证"
  → 前端调用 POST /accounts/xhs/validate
  → 后端从数据库取出 cookie
  → 调用 _validate_cookie() 向小红书 API 发送请求
  → API 返回 success=false
  → 显示"验证过期"
```

### 问题点

#### 问题 1：验证 API 请求头不完整

**位置**: `backend/app/api/v1/accounts.py` 第 224-249 行

当前代码只发送 `User-Agent` 和 `Cookie`：
```python
headers = {
    "User-Agent": "Mozilla/5.0 ...",
}
headers["Cookie"] = cookie_data
resp = await client.get(
    "https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo",
    headers=headers,
)
```

**问题**: 小红书 API 需要以下必要请求头：
- `Referer`: https://www.xiaohongshu.com/
- `Origin`: https://www.xiaohongshu.com
- 可能还需要 `x-s`, `x-t` 签名头（小红书反爬机制）

#### 问题 2：登录检测逻辑过于简单

**位置**: `backend/app/services/qrcode_login.py` 第 128-134 行

```python
def _is_logged_in(platform: str, cookies: list[dict]) -> bool:
    cookie_names = {c["name"] for c in cookies}
    if platform == "xhs":
        return "web_session" in cookie_names or "a1" in cookie_names
```

**问题**: 
- 仅检查 `web_session` 或 `a1` 存在不足以确认登录成功
- 小红书登录需要更多 cookie：`webId`, `gid`, `sec_poison_id`, `cache_bfc` 等
- 这些 cookie 可能由 JavaScript 动态生成，headless 浏览器可能未获取

#### 问题 3：Headless 浏览器 Cookie 获取不完整

**位置**: `backend/app/services/qrcode_login.py` 第 56-60 行

```python
browser = await pw.chromium.launch(
    headless=True,  # 无头模式
    channel="chrome",
    args=["--disable-blink-features=AutomationControlled"],
)
```

**问题**:
- Headless 模式下，某些 JavaScript 可能不执行
- 小红书可能检测到无头浏览器并限制功能
- 某些必要 cookie 可能由 JS 动态设置，headless 模式下未触发

#### 问题 4：Cookie 存储格式问题

**位置**: `backend/app/services/qrcode_login.py` 第 117-118 行

```python
cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
```

**问题**: 
- Cookie 值可能包含特殊字符需要转义
- 某些 cookie 的 `domain`, `path`, `httpOnly` 属性未保存

## ADDED Requirements

### Requirement: 增强小红书 Cookie 验证

系统 SHALL 在验证小红书 Cookie 时发送完整的必要请求头。

#### Scenario: 验证成功
- **WHEN** 用户点击验证按钮
- **AND** Cookie 有效
- **THEN** 系统返回 "Cookie有效"

#### Scenario: 验证失败
- **WHEN** 用户点击验证按钮
- **AND** Cookie 无效或过期
- **THEN** 系统返回 "Cookie已过期，请重新绑定"

### Requirement: 增强登录检测逻辑

系统 SHALL 检测多个关键 Cookie 来确认登录成功。

#### Scenario: 登录成功检测
- **WHEN** 扫码登录完成
- **AND** 存在 `web_session` 或 `a1` Cookie
- **AND** 存在 `webId` Cookie
- **THEN** 系统确认登录成功

### Requirement: 添加调试日志

系统 SHALL 在关键步骤添加日志，便于问题排查。

## MODIFIED Requirements

### Requirement: Cookie 验证 API 请求

修改 `_validate_cookie()` 函数，添加必要请求头：

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.xiaohongshu.com/",
    "Origin": "https://www.xiaohongshu.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
```

### Requirement: 登录检测逻辑

修改 `_is_logged_in()` 函数，检查更多必要 cookie：

```python
def _is_logged_in(platform: str, cookies: list[dict]) -> bool:
    cookie_names = {c["name"] for c in cookies}
    if platform == "xhs":
        # 必须有登录态 cookie
        has_login_cookie = "web_session" in cookie_names or "a1" in cookie_names
        # 检查是否有设备标识（可选但建议）
        has_device_id = "webId" in cookie_names or "gid" in cookie_names
        return has_login_cookie  # 暂时只检查登录态
    ...
```

## REMOVED Requirements

无移除的需求。
