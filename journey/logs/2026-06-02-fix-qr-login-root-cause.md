# 扫码登录全链路根因修复

> 日期: 2026-06-02
> 状态: DONE

## 问题

小红书和抖音扫码登录后获取的 Cookie 不完整，验证时显示"过期"；CDP 路径下扫码登录后前端自动退出登录界面。之前两次修复（`fix-xhs-login-false-positive`、`xhs-qrcode-login-validation-fix`）只修补了 Playwright 路径，CDP 路径和验证链路仍存在架构级缺陷。

## 根因分析

### 根因 1：CDP 和 Playwright 路径严重不一致

CDP 路径仍访问小红书首页（`www.xiaohongshu.com`）而非创作者登录页（`creator.xiaohongshu.com/login`），登录检测基于不可靠的按钮选择器。抖音也访问的是 `www.douyin.com` 而非 `creator.douyin.com/`。之前的修复只改了 Playwright 路径。

### 根因 2：CDP session 竞态条件（"自动退出登录界面"）

`_poll_cdp_login_status()` 登录确认后立即调用 `_cleanup_cdp_session()` 从 `_CDP_SESSIONS` 字典中移除 session。前端下次轮询时 `check_cdp_login_status()` 找不到 session，返回 "expired"。对比 Playwright 路径：`_cleanup_session()` 不从字典中移除 session，前端可以持续轮询到 "confirmed"。

### 根因 3：抖音 Cookie 验证不支持 storage_state 格式

`accounts.py` 和 `cookie_lifecycle.py` 中的抖音验证代码直接把 storage_state JSON 字符串当作 Cookie 头发送给 httpx 请求。而且抖音 API 需要签名参数，httpx 直接请求无法可靠验证。

### 根因 4：CDP `get_storage_state()` 缺失 localStorage

`cdp_browser.py` 的 `get_storage_state()` 返回 `origins: []`，丢失了 localStorage 数据。Playwright 的 `context.storage_state()` 会自动包含 localStorage。

### 根因 5：验证逻辑重复且不一致

`accounts.py` 的 `_validate_cookie()` 和 `cookie_lifecycle.py` 的 `_check_platform_login()` 实现了几乎相同的验证逻辑，但维护不同步。

## 修复方案

| 根因 | 修复 | 文件 |
|------|------|------|
| 1. CDP/Playwright 不一致 | 统一登录 URL 和登录检测逻辑 | `cdp_qrcode_login.py` |
| 2. Session 竞态 | confirmed 后保留 30 秒再清理 | `cdp_qrcode_login.py` |
| 3. 抖音验证格式错误 | 新建 Playwright 浏览器验证器 | `douyin_cookie_validator.py` (新建) |
| 4. localStorage 缺失 | 添加 `get_local_storage()` 方法 | `cdp_browser.py` |
| 5. 验证逻辑重复 | 统一到 `validate_platform_cookie()` | `cookie_lifecycle.py`, `accounts.py` |

## 关键设计决策

1. **登录 URL 统一为创作者中心**：XHS → `creator.xiaohongshu.com/login`，抖音 → `creator.douyin.com/`。参考 social-auto-upload 项目的成熟实现。

2. **登录检测策略**：不再依赖 Cookie 名称或按钮选择器，改用 URL 跳转 + 登录元素不可见的双重检测。XHS 检测 login-box 不可见，抖音检测"扫码登录"/"手机号登录"文字不可见。

3. **抖音验证改用浏览器**：与小红书一致，使用 Playwright 浏览器加载 cookie 后访问创作者中心，检查是否出现登录元素。httpx 直接请求无法通过抖音的反爬机制。

4. **Session 保留 30 秒**：CDP 路径 confirmed 后只关闭浏览器资源，session 保留在字典中 30 秒供前端轮询，与 Playwright 路径行为对齐。

## 修改文件清单

- `backend/app/services/cdp_qrcode_login.py` — 核心重写（URL、检测、二维码、session 生命周期）
- `backend/app/services/douyin_cookie_validator.py` — 新建（Playwright 浏览器验证）
- `backend/app/services/platform_scraper/cdp_browser.py` — 补全 localStorage
- `backend/app/services/cookie_lifecycle.py` — 添加统一验证入口
- `backend/app/api/v1/accounts.py` — 验证逻辑委托统一入口

## 教训

1. **双路径必须同步修改**：CDP 和 Playwright 两条路径共享相同的业务逻辑，修改一条路径时必须同步修改另一条，否则会出现行为不一致。
2. **Session 生命周期需要考虑消费者**：后端清理 session 时必须考虑前端轮询的时序，不能在消费者（前端）确认之前就销毁资源。
3. **验证方式必须与存储格式匹配**：存储格式改为 storage_state 后，验证代码也必须适配，否则验证必然失败。
4. **重复代码是 bug 的温床**：`accounts.py` 和 `cookie_lifecycle.py` 各自实现验证逻辑，导致修改时容易遗漏。
