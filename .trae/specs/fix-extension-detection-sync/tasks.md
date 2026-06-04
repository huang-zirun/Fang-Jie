# Tasks

- [x] Task 1: 修复 content script 消息过滤逻辑
  - [x] SubTask 1.1: 移除 `extension/content.js` 中 `if (event.source !== window) return;` 检查
  - [x] SubTask 1.2: 验证保留 `event.data.source === "intent-money-extension"` 循环防护足够
  - [x] SubTask 1.3: 测试页面 PING → content script PONG 通信链路恢复

- [x] Task 2: 实现扩展状态广播通道
  - [x] SubTask 2.1: 在 `extension/background.js` 中新增 `BROADCAST_STATUS` message handler
  - [x] SubTask 2.2: 修改 `chrome.cookies.onChanged` 监听器，变化时查询所有激活标签页并广播状态
  - [x] SubTask 2.3: 在 `extension/content.js` 中新增 `INTENT_MONEY_STATUS_UPDATE` 广播发送逻辑
  - [x] SubTask 2.4: 修改 `syncCookiesToBackend`，`authToken` 缺失时记录 warn 但继续尝试同步

- [x] Task 3: 重构前端扩展检测机制
  - [x] SubTask 3.1: 重写 `checkExtension()` 为指数退避重试（最多 5 次，间隔 1s/2s/3s/4s/5s）
  - [x] SubTask 3.2: 添加页面 `visibilitychange` 监听，页面重新可见时触发重检
  - [x] SubTask 3.3: 检测成功后立即调用 `configureExtension()` 同步 authToken 和 serverUrl
  - [x] SubTask 3.4: 组件卸载时清理所有定时器和事件监听器

- [x] Task 4: 前端扩展状态同步与 UI 展示
  - [x] SubTask 4.1: 新增 `extensionStatus` 响应式对象（结构：`{ xhs: {...}, douyin: {...} }`）
  - [x] SubTask 4.2: 添加全局 `message` 事件监听，接收 `INTENT_MONEY_STATUS_UPDATE` 并更新 `extensionStatus`
  - [x] SubTask 4.3: 在账号卡片上显示扩展登录状态标识（"浏览器已登录"绿色圆点）
  - [x] SubTask 4.4: 扩展检测到已登录但后端未绑定时，显示"同步到后端"按钮
  - [x] SubTask 4.5: 点击"同步到后端"调用 `handleFetchCookies()` 将扩展 cookie 同步到后端

- [x] Task 5: 验证修复效果
  - [x] SubTask 5.1: 清除扩展存储，刷新页面，确认前端能检测到扩展并显示"扩展已连接"
  - [x] SubTask 5.2: 在小红书/抖音网站登录，确认扩展 popup 显示"已登录"
  - [x] SubTask 5.3: 确认前端收到 `INTENT_MONEY_STATUS_UPDATE` 并显示"浏览器已登录"
  - [x] SubTask 5.4: 点击"同步到后端"，确认后端账号变为"已绑定"且 cookie 有效
  - [x] SubTask 5.5: 解绑账号后，确认扩展状态仍正确显示，可再次同步
  - [x] SubTask 5.6: 测试扩展未安装场景，前端正确显示"未检测到浏览器扩展"

# Task Dependencies

- [Task 2] depends on [Task 1] (广播通道依赖 content script 能正确收发消息)
- [Task 3] depends on [Task 1] (前端检测依赖 content script 响应 PING)
- [Task 4] depends on [Task 2] 和 [Task 3] (状态显示依赖广播通道和检测机制)
- [Task 5] depends on [Task 1] and [Task 2] and [Task 3] and [Task 4]
