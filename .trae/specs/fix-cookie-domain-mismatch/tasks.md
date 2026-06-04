# Tasks

- [x] Task 1: 后端 Cookie domain 规范化
  - [x] SubTask 1.1: 在 `accounts.py` 中定义平台域名映射常量 `_PLATFORM_DOMAINS`
  - [x] SubTask 1.2: 实现 `_normalize_cookie_domain(domain: str, platform: str) -> str` 函数
  - [x] SubTask 1.3: 在 `extension_cookie_login` 函数中调用 domain 规范化

- [x] Task 2: 扩展 CHECK_LOGIN 状态检测修复
  - [x] SubTask 2.1: 修改 `background.js` 的 `CHECK_LOGIN` handler，将 `loggedIn` 判断从 `!sessionCookie.session` 改为 `!!sessionCookie.value`
  - [x] SubTask 2.2: 同步修改 `chrome.cookies.onChanged` 监听器中的 `loggedIn` 判断逻辑
  - [x] SubTask 2.3: 同步修改 `SYNC_COOKIES` 和 `BROADCAST_STATUS` handler 中的 `loggedIn` 判断逻辑

# Task Dependencies

- Task 1 和 Task 2 相互独立，可并行执行
