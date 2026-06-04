# Cookie Domain 子域隔离导致验证始终"过期"

> 日期: 2026-06-03
> 状态: DONE
> Spec: `.trae/specs/fix-cookie-domain-mismatch/`

## 现象

用户在浏览器中正常登录了小红书和抖音，扩展 popup 显示抖音已登录但小红书获取失败。同步到后端后，点击两个平台的"验证"都显示 Cookie 已过期。

## 根因

### 根因 1：Cookie domain 子域隔离

完整链路：

1. 用户在浏览器中访问 `www.xiaohongshu.com` 并登录
2. 浏览器设置的 `web_session` Cookie 的 domain 可能是 `.xiaohongshu.com`（跨子域共享），也可能是 `www.xiaohongshu.com`（仅限 www 子域）
3. 扩展调用 `chrome.cookies.getAll({ domain: ".xiaohongshu.com" })` 获取所有 Cookie，**保留了原始 domain 字段**
4. 后端 `extension_cookie_login` 将 Cookie 转换为 `storage_state` 格式，**domain 原样保留**
5. 验证器用 Playwright 加载 `storage_state`，访问 `creator.xiaohongshu.com/publish/publish`
6. Playwright 遵循 RFC 6265，domain 为 `www.xiaohongshu.com` 的 Cookie **不会**被发送到 `creator.xiaohongshu.com`
7. 验证器没有有效的登录 Cookie，被重定向到登录页，返回"过期"

抖音同理：用户在 `www.douyin.com` 登录，验证器访问 `creator.douyin.com`。

### 根因 2：扩展 CHECK_LOGIN 误判

`loggedIn` 判断条件 `!!sessionCookie && !sessionCookie.session` 依赖 Cookie 是否为会话 Cookie。小红书的 `web_session` 可能是会话 Cookie（`session: true`），导致 `loggedIn` 为 `false`，扩展 popup 显示"未登录"。

### 与之前修复的关系

之前（同日早些时候）修复了 sameSite 转换、expires 字段名、平台名称映射三个 Bug，但这些都是 Cookie 格式转换的问题。**Cookie domain 子域隔离**是一个更深层的架构问题：存储的 Cookie domain 与验证器访问的域名不在同一个子域。之前的修复只是让 Cookie 能被正确解析，但没有解决域名不匹配导致的跨子域不可用问题。

## 修复

### accounts.py

1. 新增 `_PLATFORM_DOMAINS` 常量：`{"xhs": ".xiaohongshu.com", "douyin": ".douyin.com"}`
2. 新增 `_normalize_cookie_domain(domain, platform)` 函数：将子域名统一规范化为父域名
3. `extension_cookie_login` 中调用规范化：`"domain": _normalize_cookie_domain(c["domain"], platform)`

### background.js

4 处 `loggedIn` 判断从 `!!sessionCookie && !sessionCookie.session` 改为 `!!sessionCookie && !!sessionCookie.value`：
- `chrome.cookies.onChanged` 监听器
- `CHECK_LOGIN` handler
- `SYNC_COOKIES` handler
- `BROADCAST_STATUS` handler

## 设计决策

- **在后端做 domain 规范化而非改扩展**：扩展通过 `chrome.cookies.getAll` 获取的 Cookie domain 是浏览器存储的原始值，不应在扩展侧篡改。后端作为数据转换层，负责确保存储格式兼容 Playwright。
- **规范化为父域名而非改验证器访问 www 子域**：验证器访问创作者中心（`creator.xiaohongshu.com`）是业务需求（验证是否能发布内容），不应降级到主站。将 Cookie domain 提升为父域名是更正确的做法，确保所有子域都能共享登录态。
- **用 `!!sessionCookie.value` 替代 `!sessionCookie.session`**：Cookie 是否有值是判断登录态的可靠标准，而 `session` 属性只表示 Cookie 是否有过期时间，与登录态无关。
