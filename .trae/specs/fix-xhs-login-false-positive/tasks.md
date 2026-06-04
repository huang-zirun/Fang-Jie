# Tasks

- [x] Task 1: 重写 qrcode_login.py 扫码登录流程
  - [x] SubTask 1.1: 修改 PLATFORM_LOGIN_URLS，小红书改为 `https://creator.xiaohongshu.com/login`
  - [x] SubTask 1.2: 删除 `_is_logged_in()` 函数，改用页面 URL 跳转检测
  - [x] SubTask 1.3: 重写 `_poll_login_status()`，使用页面 URL 变化判断登录成功
  - [x] SubTask 1.4: 修改登录成功后的状态保存，使用 `context.storage_state()` 替代 Cookie 字符串拼接
  - [x] SubTask 1.5: 修改 `check_login_status()` 返回 storage_state JSON 而非 cookie_str

- [x] Task 2: 适配 accounts.py 的 storage_state 格式
  - [x] SubTask 2.1: 修改 `check_qrcode_status()` 处理 storage_state JSON
  - [x] SubTask 2.2: 修改 `_validate_cookie()` 适配 storage_state 格式

- [x] Task 3: 适配 xhs_cookie_validator.py 的 storage_state 格式
  - [x] SubTask 3.1: 修改 `validate_xhs_cookie_via_browser()` 支持 storage_state JSON 输入
  - [x] SubTask 3.2: 确保验证使用 `browser.new_context(storage_state=...)` 加载状态

- [x] Task 4: 验证修复效果
  - [x] SubTask 4.1: 测试未扫码时不会误判为"已登录"
  - [x] SubTask 4.2: 测试扫码登录成功后验证显示"有效"

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2] and [Task 3]
