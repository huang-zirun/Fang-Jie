# Tasks

- [x] Task 1: 开发 Chrome Extension 基础框架
  - [x] SubTask 1.1: 创建 Manifest V3 项目结构（manifest.json, background.js, popup.html, popup.js, content.js, icons）
  - [x] SubTask 1.2: 实现 `chrome.cookies.getAll()` 读取小红书 Cookie 的核心逻辑
  - [x] SubTask 1.3: 实现 `chrome.cookies.onChanged` 监听，自动检测 Cookie 变化
  - [x] SubTask 1.4: 实现 popup UI（显示 Cookie 状态、一键获取按钮）
  - [x] SubTask 1.5: 实现与前端页面的 `window.postMessage` 通信协议
  - [x] SubTask 1.6: 实现引导登录功能（打开 XHS 标签页，检测登录完成）

- [x] Task 2: 后端 API 适配
  - [x] SubTask 2.1: 新增 `POST /accounts/{platform}/extension` 端点，接收扩展发送的 Cookie
  - [x] SubTask 2.2: 实现 Chrome Cookie 格式 → Playwright `storage_state` 格式转换
  - [x] SubTask 2.3: 复用现有 CookieVault 加密存储逻辑
  - [x] SubTask 2.4: 添加请求来源校验（防止 Cookie 伪造）

- [x] Task 3: 前端扩展集成
  - [x] SubTask 3.1: 实现扩展安装检测逻辑（通过 postMessage 心跳）
  - [x] SubTask 3.2: 扩展已安装时，"扫码登录"改为"一键登录"
  - [x] SubTask 3.3: 扩展未安装时，显示安装引导 + 保留降级方案
  - [x] SubTask 3.4: 实现扩展登录成功通知的 UI 更新

- [x] Task 4: 登录优先级调度
  - [x] SubTask 4.1: 前端登录流程按优先级调度：Extension → CDP → Playwright
  - [x] SubTask 4.2: 后端新增扩展登录 API 的路由注册

- [ ] Task 5: 测试与验证
  - [ ] SubTask 5.1: 手动测试扩展 Cookie 获取（含 httpOnly）
  - [ ] SubTask 5.2: 测试引导登录完整流程
  - [ ] SubTask 5.3: 测试 Cookie 自动续期
  - [ ] SubTask 5.4: 测试降级方案（扩展未安装时回退到 CDP/Playwright）

# Task Dependencies
- [Task 2] depends on [Task 1] (后端需要知道扩展发送的 Cookie 格式)
- [Task 3] depends on [Task 1] (前端需要知道扩展的通信协议)
- [Task 4] depends on [Task 2, Task 3]
- [Task 5] depends on [Task 1, Task 2, Task 3, Task 4]
