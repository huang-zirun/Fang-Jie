# Checklist

- [x] PLATFORM_LOGIN_URLS 中小红书 URL 改为 `https://creator.xiaohongshu.com/login`
- [x] 删除了 `_is_logged_in()` 函数，不再基于 Cookie 名称检测
- [x] `_poll_login_status()` 使用页面 URL 跳转检测登录成功
- [x] 登录成功后使用 `context.storage_state()` 保存完整状态
- [x] `check_login_status()` 返回 storage_state JSON
- [x] `accounts.py` 的 `check_qrcode_status()` 处理 storage_state JSON
- [x] `xhs_cookie_validator.py` 支持 storage_state 格式验证
- [x] 未扫码时不会误判为"已登录"
- [x] 扫码登录成功后验证显示"有效"
