# Tasks

- [x] Task 1: 统一 CDP 路径的登录 URL 和登录检测逻辑
  - [x] SubTask 1.1: 修改 `cdp_qrcode_login.py` 中 `PLATFORM_LOGIN_URLS`，XHS 改为 `https://creator.xiaohongshu.com/login`，抖音改为 `https://creator.douyin.com/`
  - [x] SubTask 1.2: 修改 `cdp_qrcode_login.py` 中 `PLATFORM_LOGIN_URL_PREFIXES`，XHS 改为 `https://creator.xiaohongshu.com/login`，抖音改为 `https://creator.douyin.com/login`
  - [x] SubTask 1.3: 重写 `_check_login_done()` 函数，XHS 使用 URL 跳转 + login-box 不可见检测，抖音使用 URL 跳转到 creator-micro/home + 登录元素不可见检测
  - [x] SubTask 1.4: 修改 `_capture_qr_screenshot()` 中 XHS 的二维码截取逻辑，适配创作者中心登录页的 DOM 结构（参考 social-auto-upload 的 `_open_xhs_qrcode_panel` 和 `_find_xhs_qrcode_locator`）
  - [x] SubTask 1.5: 修改 `_capture_qr_screenshot()` 中抖音的二维码截取逻辑，适配创作者中心登录页（参考 social-auto-upload 的 `_extract_douyin_qrcode_src`）

- [x] Task 2: 修复 CDP session 生命周期（"自动退出登录界面"问题）
  - [x] SubTask 2.1: 修改 `_cleanup_cdp_session()`，不再立即从 `_CDP_SESSIONS` 中移除 confirmed 状态的 session，改为标记清理时间
  - [x] SubTask 2.2: 在 `CdpQrLoginSession` 中添加 `confirmed_at` 字段，记录确认时间
  - [x] SubTask 2.3: 修改 `_poll_cdp_login_status()`，登录确认后设置 `confirmed_at` 并关闭浏览器资源，但不从字典中移除
  - [x] SubTask 2.4: 修改 `cleanup_expired_cdp_sessions()`，同时清理 confirmed 超过 30 秒的 session

- [x] Task 3: 补全 CDP `get_storage_state()` 的 localStorage 数据
  - [x] SubTask 3.1: 在 `cdp_browser.py` 中添加 `get_local_storage()` 方法，通过 `Runtime.evaluate` 获取当前页面 localStorage
  - [x] SubTask 3.2: 修改 `get_storage_state()` 方法，调用 `get_local_storage()` 并将结果格式化为 Playwright origins 格式

- [x] Task 4: 重写抖音 Cookie 验证为浏览器验证方式
  - [x] SubTask 4.1: 创建 `backend/app/services/douyin_cookie_validator.py`，实现 `validate_douyin_cookie(cookie_data: str) -> bool`
  - [x] SubTask 4.2: 支持 storage_state JSON 和 cookie_string 两种格式
  - [x] SubTask 4.3: 使用 Playwright 浏览器加载 cookie，访问 `https://creator.douyin.com/creator-micro/content/upload`
  - [x] SubTask 4.4: 检查是否出现"扫码登录"或"手机号登录"文字，未出现则返回 True

- [x] Task 5: 统一验证入口
  - [x] SubTask 5.1: 在 `cookie_lifecycle.py` 中创建 `validate_platform_cookie(platform: str, cookie_data: str) -> bool` 统一验证函数
  - [x] SubTask 5.2: 修改 `accounts.py` 的 `_validate_cookie()` 调用 `validate_platform_cookie()`
  - [x] SubTask 5.3: 修改 `cookie_lifecycle.py` 的 `_check_platform_login()` 调用 `validate_platform_cookie()`
  - [x] SubTask 5.4: 删除 `accounts.py` 和 `cookie_lifecycle.py` 中的重复验证代码

- [x] Task 6: 验证修复效果
  - [x] SubTask 6.1: 测试 CDP 路径小红书扫码登录，确认访问创作者中心登录页
  - [x] SubTask 6.2: 测试 CDP 路径抖音扫码登录，确认访问创作者中心
  - [x] SubTask 6.3: 测试扫码登录成功后前端显示"登录成功"而非"二维码已过期"
  - [x] SubTask 6.4: 测试小红书验证功能，确认 storage_state 格式验证通过
  - [x] SubTask 6.5: 测试抖音验证功能，确认浏览器验证方式正常工作
  - [x] SubTask 6.6: 测试 Playwright 降级路径仍正常工作

# Task Dependencies

- [Task 2] depends on [Task 1] (session 生命周期修复依赖登录检测逻辑正确)
- [Task 3] depends on [Task 1] (localStorage 获取依赖正确的登录 URL)
- [Task 5] depends on [Task 4] (统一验证入口依赖抖音验证器实现)
- [Task 6] depends on [Task 1] and [Task 2] and [Task 3] and [Task 4] and [Task 5]
