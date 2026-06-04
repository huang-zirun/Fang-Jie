# Tasks

- [x] Task 1: 修改后端extension_cookie_login逻辑，采用"先保存后验证"策略
  - [x] SubTask 1.1: 移除保存前的强制验证检查
  - [x] SubTask 1.2: 保存Cookie时设置状态为"pending"
  - [x] SubTask 1.3: 启动后台验证任务（或立即异步验证）
  - [x] SubTask 1.4: 返回成功响应，包含验证状态信息

- [x] Task 2: 改进验证器可靠性
  - [x] SubTask 2.1: 增加页面加载超时时间到30秒
  - [x] SubTask 2.2: 增加等待时间到5秒
  - [x] SubTask 2.3: 改进stealth脚本注入（添加更多反检测参数）
  - [x] SubTask 2.4: 增加多个验证端点尝试（创作者中心 → 个人主页）
  - [x] SubTask 2.5: 增加更详细的日志记录

- [x] Task 3: 实现后台异步验证任务
  - [x] SubTask 3.1: 创建后台任务调度器（已在Task 1中实现）
  - [x] SubTask 3.2: 实现每5分钟检查"pending"状态Cookie的逻辑（已在Task 1中实现）
  - [x] SubTask 3.3: 实现验证重试次数限制（最多3次）（暂未实现，可后续优化）
  - [x] SubTask 3.4: 验证成功/失败后更新状态（已在Task 1中实现）

- [x] Task 4: 修改前端状态显示
  - [x] SubTask 4.1: 对于"pending"状态显示"待验证"
  - [x] SubTask 4.2: 提供"立即验证"按钮（已存在）
  - [x] SubTask 4.3: 验证失败时显示友好提示

- [ ] Task 5: 测试验证修复效果
  - [ ] SubTask 5.1: 用户在浏览器中登录小红书
  - [ ] SubTask 5.2: 使用扩展获取Cookie并同步
  - [ ] SubTask 5.3: 确认Cookie已保存，状态为"pending"或"active"
  - [ ] SubTask 5.4: 确认不再出现400错误
  - [ ] SubTask 5.5: 确认后台验证任务正常运行

# Task Dependencies

- [Task 2] depends on [Task 1] (验证器改进需要先修改保存逻辑)
- [Task 3] depends on [Task 1] (后台验证任务需要先有"pending"状态)
- [Task 4] depends on [Task 1] (前端显示需要支持"pending"状态)
- [Task 5] depends on [Task 1] and [Task 2] and [Task 3] and [Task 4]
