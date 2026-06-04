# Tasks

- [x] Task 1: 调查验证 API 失败的具体原因
  - [x] SubTask 1.1: 添加调试日志到 `_validate_cookie()` 函数，记录请求和响应详情
  - [x] SubTask 1.2: 手动测试验证 API，确认需要哪些请求头
  - [x] SubTask 1.3: 检查数据库中存储的 cookie 内容是否完整

- [x] Task 2: 修复 Cookie 验证请求头
  - [x] SubTask 2.1: 修改 `accounts.py` 中 `_validate_cookie()` 添加必要请求头
  - [x] SubTask 2.2: 修改 `cookie_lifecycle.py` 中 `_check_platform_login()` 添加相同请求头

- [x] Task 3: 增强登录检测逻辑
  - [x] SubTask 3.1: 修改 `qrcode_login.py` 中 `_is_logged_in()` 检查更多 cookie
  - [x] SubTask 3.2: 添加登录成功时的 cookie 列表日志

- [x] Task 4: 验证修复效果
  - [x] SubTask 4.1: 测试扫码登录流程
  - [x] SubTask 4.2: 测试验证功能

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2] and [Task 3]
