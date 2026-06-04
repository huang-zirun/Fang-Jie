# Tasks

- [ ] Task 1: 扩展 content_scripts 匹配范围修复
  - [ ] SubTask 1.1: 修改 `manifest.json` 的 `content_scripts.matches` 从 `["http://localhost:*/*", "http://127.0.0.1:*/*"]` 改为 `["<all_urls>"]`
  - [ ] SubTask 1.2: 验证修改后 localhost、127.0.0.1、Docker IP、局域网 IP 等 URL 均能注入 content script

- [ ] Task 2: 扩展新增 SET_COOKIES 功能（QR 登录后注入 Cookie 到真实浏览器）
  - [ ] SubTask 2.1: 在 `background.js` 中新增 `SET_COOKIES` message handler，接收 platform + cookies 数组
  - [ ] SubTask 2.2: SET_COOKIES handler 内遍历 cookies，对每个 cookie 调用 `chrome.cookies.set()` 写入真实浏览器（使用正确的 url/domain/path/httpOnly/secure/sameSite 参数）
  - [ ] SubTask 2.3: 返回 `{ success: true, setCount, failCount }` 结果，包含失败 cookie 的错误信息
  - [ ] SubTask 2.4: 在 `content.js` 中新增 `INTENT_MONEY_SET_COOKIES` 消息监听器，转发到 background.js

- [ ] Task 3: 前端 QR 登录确认后触发 Cookie 同步到扩展
  - [ ] SubTask 3.1: 在 `AccountManage.vue` 的 QR 轮询 `confirmed` 分支中，fetchAccounts() 之后增加 Cookie 同步逻辑
  - [ ] SubTask 3.2: 新增 `syncCookiesToExtension(platform, storageState)` 函数：通过 postMessage 发送 `INTENT_MONEY_SET_COOKIES` 给扩展
  - [ ] SubTask 3.3: 若扩展未安装（extensionInstalled=false），跳过同步但记录日志不报错
  - [ ] SubTask 3.4: 后端 `check_qrcode_status` API 在 confirmed 状态时返回 `storage_state` 数据给前端（当前已返回，确认字段完整）

- [ ] Task 4: 扩展 CHECK_LOGIN 增加后端 API 降级查询
  - [ ] SubTask 4.1: 在 `background.js` 的 `CHECK_LOGIN` handler 中，当本地 Cookie 检测为未登录时，增加后端 API 查询
  - [ ] SubTask 4.2: 新增后端 API 端点 `GET /accounts/{platform}/bind-status`（或复用现有 GET /accounts/ 返回数据），返回 bind_status 和 cookie_status
  - [ ] SubTask 4.3: CHECK_LOGIN 返回值增加 `source: "local" | "backend"` 字段标识数据来源
  - [ ] SubTask 4.4: 修改 `popup.js` 的 `checkLoginStatus()` 根据 source 显示不同样式

- [ ] Task 5: 扩展 popup UI 区分登录状态来源
  - [ ] SubTask 5.1: 修改 `popup.html` 登录状态区域，增加来源标注（"本地Cookie" / "服务端同步"）
  - [ ] SubTask 5.2: 修改 `popup.js` 根据 CHECK_LOGIN 返回的 source 字段显示不同的状态点和文字
  - [ ] SubTask 5.3: "服务端同步"的已登录状态使用虚线圆点或不同颜色区分

- [ ] Task 6: 前端扩展检测与账号状态展示解耦
  - [ ] SubTask 6.1: 确保 QR 登录成功后的 `fetchAccounts()` 正确更新 accounts 列表（当前实现已正确，验证即可）
  - [ ] SubTask 6.2: 顶部扩展提示区保持独立，不影响下方账号卡片的正确显示
  - [ ] SubTask 6.3: QR 弹窗 confirmed → success 显示 → 自动关闭的时序验证无误

# Task Dependencies

- [Task 2] depends on [Task 1]（SET_COOKIES 功能依赖 content script 能正常注入）
- [Task 3] depends on [Task 2]（前端同步逻辑依赖扩展已支持 SET_COOKIES）
- [Task 4] 无依赖，可与 Task 1-3 并行
- [Task 5] depends on [Task 4]（popup UI 依赖 CHECK_LOGIN 返回新字段）
- [Task 6] 无依赖，可与 Task 1-5 并行
