# Cookie 域名不匹配导致验证始终"过期" Spec

## Why

用户在浏览器中正常登录了小红书和抖音，但账号管理页面显示 Cookie 已过期。扩展获取小红书状态失败，同步后验证两个平台都显示过期。根本原因是：扩展获取的 Cookie 保留了原始子域名（如 `www.xiaohongshu.com`），但验证器访问的是创作者子域名（`creator.xiaohongshu.com`），Playwright 不会将 `www` 子域的 Cookie 发送到 `creator` 子域，导致验证始终失败。

## What Changes

- **BREAKING** 在后端 `extension_cookie_login` 中，将扩展传来的 Cookie domain 统一规范化为父域名（如 `www.xiaohongshu.com` → `.xiaohongshu.com`），确保 Playwright 在访问任何子域时都能携带 Cookie
- 修复扩展 `CHECK_LOGIN` 对小红书的状态检测逻辑，`web_session` 是 httpOnly Cookie，`session` 属性可能为 `true`（会话 Cookie），导致误判为"未登录"

## Impact

- Affected specs: fix-extension-detection-sync, same-browser-xhs-cookie, fix-xhs-login-false-positive
- Affected code:
  - `backend/app/api/v1/accounts.py` — `extension_cookie_login` 函数，Cookie domain 规范化
  - `extension/background.js` — `CHECK_LOGIN` handler，修复小红书状态检测

## 根因分析

### 根因 1：Cookie domain 子域隔离导致验证失败

**完整链路**：

1. 用户在浏览器中访问 `www.xiaohongshu.com` 并登录
2. 浏览器设置的 `web_session` Cookie 的 domain 可能是 `.xiaohongshu.com`（跨子域共享），也可能是 `www.xiaohongshu.com`（仅限 www 子域）
3. 扩展调用 `chrome.cookies.getAll({ domain: ".xiaohongshu.com" })` 获取所有 Cookie，**保留了原始 domain 字段**
4. 扩展将 Cookie 发送到后端 `POST /accounts/xiaohongshu/extension`
5. 后端 `extension_cookie_login` 将 Cookie 转换为 `storage_state` 格式，**domain 原样保留**
6. 用户点击"验证"，后端调用 `validate_xhs_cookie()`
7. 验证器用 Playwright 加载 `storage_state`，访问 `creator.xiaohongshu.com/publish/publish`
8. **关键问题**：Playwright 的 Cookie 机制遵循 RFC 6265，domain 为 `www.xiaohongshu.com` 的 Cookie **不会**被发送到 `creator.xiaohongshu.com`
9. 验证器没有有效的登录 Cookie，被重定向到登录页，返回"过期"

**同样的问题也影响抖音**：用户在 `www.douyin.com` 登录，验证器访问 `creator.douyin.com`。

**关键代码位置**：

`accounts.py` 第 118-133 行 — `extension_cookie_login` 函数：
```python
converted = {
    "name": c["name"],
    "value": c["value"],
    "domain": c["domain"],  # ← 原样保留，可能是 www.xiaohongshu.com
    "path": c.get("path", "/"),
    ...
}
```

`xhs_cookie_validator.py` 第 7-8 行 — 验证器访问的 URL：
```python
XHS_LOGIN_URL = "https://creator.xiaohongshu.com/login"
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"
```

`douyin_cookie_validator.py` 第 7 行 — 验证器访问的 URL：
```python
DOUYIN_CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"
```

### 根因 2：扩展 CHECK_LOGIN 对小红书误判

`background.js` 第 133-139 行 — `CHECK_LOGIN` handler：
```javascript
const sessionCookie = cookies.find((c) => c.name === cfg.sessionCookie);
sendResponse({
    success: true,
    loggedIn: !!sessionCookie && !sessionCookie.session,  // ← 问题在这里
    ...
});
```

`loggedIn` 的判断条件是 `!!sessionCookie && !sessionCookie.session`。`session` 属性表示 Cookie 是否为会话 Cookie（无过期时间）。小红书的 `web_session` Cookie 名称虽然带 "session"，但它可能是持久 Cookie（有过期时间），也可能是会话 Cookie。如果是会话 Cookie（`session: true`），则 `loggedIn` 为 `false`，扩展 popup 显示"未登录"。

但更关键的是：即使 `web_session` 是持久 Cookie，如果它的 domain 是 `www.xiaohongshu.com` 而非 `.xiaohongshu.com`，`chrome.cookies.getAll({ domain: ".xiaohongshu.com" })` 仍然能获取到它（因为 Chrome API 的 domain 参数是"包含"匹配），但 `sessionCookie.session` 的值取决于 Cookie 本身的属性。

**实际上**，小红书的 `web_session` Cookie 很可能确实是持久 Cookie（有过期时间），所以 `session` 应该为 `false`。用户报告"小红书获取失败"更可能是因为 `web_session` Cookie 根本不在 `chrome.cookies.getAll({ domain: ".xiaohongshu.com" })` 的返回结果中——这可能是因为用户登录的站点域名与扩展查询的域名不完全匹配。

### 为什么之前的修复没有解决

之前修复了 sameSite 转换、expires 字段名、平台名称映射等问题，但这些都是 Cookie 格式转换的问题。**Cookie domain 子域隔离**是一个更深层的架构问题：存储的 Cookie domain 与验证器访问的域名不在同一个子域。

## ADDED Requirements

### Requirement: Cookie domain 规范化

后端在接收扩展传来的 Cookie 并转换为 `storage_state` 格式时，SHALL 将所有 Cookie 的 domain 规范化为父域名，确保 Playwright 在访问任何子域时都能携带 Cookie。

规范化规则：
- `www.xiaohongshu.com` → `.xiaohongshu.com`
- `creator.xiaohongshu.com` → `.xiaohongshu.com`
- 任何 `*.xiaohongshu.com` → `.xiaohongshu.com`
- `www.douyin.com` → `.douyin.com`
- `creator.douyin.com` → `.douyin.com`
- 任何 `*.douyin.com` → `.douyin.com`
- 已经是 `.xiaohongshu.com` 或 `.douyin.com` 的保持不变

#### Scenario: 扩展传来 www 子域的 Cookie
- **WHEN** 扩展发送 Cookie，其中 `web_session` 的 domain 为 `www.xiaohongshu.com`
- **THEN** 后端将其规范化为 `.xiaohongshu.com`
- **AND** 存储到数据库的 `storage_state` 中 domain 为 `.xiaohongshu.com`
- **AND** Playwright 加载此 `storage_state` 后访问 `creator.xiaohongshu.com` 时能携带该 Cookie

#### Scenario: 扩展传来已经是父域名的 Cookie
- **WHEN** 扩展发送 Cookie，domain 已经是 `.xiaohongshu.com`
- **THEN** 后端保持不变

#### Scenario: 抖音 Cookie domain 规范化
- **WHEN** 扩展发送抖音 Cookie，domain 为 `www.douyin.com`
- **THEN** 后端将其规范化为 `.douyin.com`

### Requirement: 扩展 CHECK_LOGIN 状态检测修复

扩展的 `CHECK_LOGIN` handler SHALL 改进小红书登录状态检测逻辑，不再依赖 `!sessionCookie.session` 判断，而是检查关键 Cookie 是否存在且非空。

#### Scenario: 小红书 web_session Cookie 存在且为会话 Cookie
- **WHEN** `chrome.cookies.getAll` 返回的 Cookie 中包含 `web_session`
- **AND** `web_session.session` 为 `true`（会话 Cookie）
- **THEN** `CHECK_LOGIN` 返回 `loggedIn: true`
- **AND** 扩展 popup 显示"已登录"

#### Scenario: 小红书 web_session Cookie 不存在
- **WHEN** `chrome.cookies.getAll` 返回的 Cookie 中不包含 `web_session`
- **THEN** `CHECK_LOGIN` 返回 `loggedIn: false`
- **AND** 扩展 popup 显示"未登录"

## MODIFIED Requirements

### Requirement: extension_cookie_login Cookie 转换

修改 `accounts.py` 的 `extension_cookie_login` 函数，在 Cookie 转换步骤中增加 domain 规范化逻辑：

1. 定义平台域名映射：`{"xhs": ".xiaohongshu.com", "douyin": ".douyin.com"}`
2. 对每个 Cookie 的 domain 进行规范化：如果 domain 以平台父域名结尾但不是父域名本身，则替换为父域名
3. 规范化规则：匹配 `^(.+\.)?xiaohongshu\.com$` → `.xiaohongshu.com`，`^(.+\.)?douyin\.com$` → `.douyin.com`

### Requirement: 扩展 CHECK_LOGIN handler

修改 `extension/background.js` 的 `CHECK_LOGIN` handler：

1. 将 `loggedIn` 判断从 `!!sessionCookie && !sessionCookie.session` 改为 `!!sessionCookie && !!sessionCookie.value`
2. 保留 `cookieExists` 字段用于调试

## REMOVED Requirements

（无移除需求）
