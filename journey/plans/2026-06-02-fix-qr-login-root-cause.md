# 扫码登录全链路根因修复计划

> 日期: 2026-06-02
> 状态: DONE

## 目标

从根因出发统一修复小红书和抖音扫码登录的 Cookie 不完整、验证过期、CDP 路径自动退出登录界面三个问题，拒绝 ad hoc patch。

## 修复范围

5 个根因，6 个任务，5 个文件修改 + 1 个新建文件。

## 任务分解

1. **统一 CDP 路径登录 URL 和检测逻辑** — 修改 `cdp_qrcode_login.py`，与 Playwright 路径对齐
2. **修复 CDP session 生命周期** — confirmed 后保留 30 秒，不立即移除
3. **补全 CDP localStorage** — `cdp_browser.py` 添加 `get_local_storage()`
4. **新建抖音浏览器验证器** — `douyin_cookie_validator.py`
5. **统一验证入口** — `validate_platform_cookie()` 消除重复代码
6. **验证修复效果** — 17 项检查全部通过

## 依赖关系

- Task 2, 3 依赖 Task 1
- Task 5 依赖 Task 4
- Task 6 依赖所有前置任务

## 结果

所有 6 个任务完成，17 项检查全部通过，Python 编译验证通过。
