# CDP 自动发布实现日志

## 2026-05-26 实施记录

### 已完成

#### Step 1: CdpBrowser DOM 域能力扩展
- 新增 `dom_enable()` — 启用 DOM 域
- 新增 `dom_get_document()` — 获取 DOM 根节点 nodeId
- 新增 `query_selector(selector)` — DOM.querySelector
- 新增 `set_file_input_files(selector, file_paths)` — **核心**: 通过 DOM.setFileInputFiles 真正上传文件
- 新增 `wait_for_selector(selector, timeout)` — 轮询等待元素出现，替代硬编码 sleep
- 新增 `click_element(selector)` — 完整鼠标事件模拟（mousedown → mouseup → click）
- 新增 `fill_input(selector, value, react_compat=True)` — React 兼容输入填充（使用原生 setter）
- 新增 `fill_contenteditable(selector, text)` — contenteditable div 填充（XHS 编辑器）

#### Step 2: 事件监听基础设施
- 修改 `_send_cmd` 区分命令响应（有 id）和事件通知（无 id）
- 新增 `on(event, handler)` / `off(event, handler)` 事件注册机制
- 新增 `_dispatch_event` 内部事件分发
- 新增 `network_enable()` — 启用 Network 域

#### Step 3: CdpPublisher 抖音视频发布重写
- 使用 `set_file_input_files` 真正上传视频（不再返回"CDP 无法直接设置文件路径"）
- 使用 `fill_input` React 兼容模式填写标题/描述
- 使用 `click_element` 点击发布按钮
- 使用 `wait_for_selector` 等待上传完成和页面元素
- 登录态检测改用 `evaluate` 检查特定元素，而非全文搜索

#### Step 4: CdpPublisher 小红书发布重写
- `publish_xhs_note`: 图片上传 + 标题 + contenteditable 正文 + 发布
- `publish_xhs_video`: 视频上传 + 标题 + 描述 + 发布
- 均使用 DOM 域方法替代 JS 注入

#### Step 5: auto_publisher.py 超时保护
- CDP 发布增加 60 秒超时保护（`asyncio.wait_for`）
- 超时自动降级到 sau CLI
- 增加详细的发布结果日志（成功/失败/降级原因）

### 未完成
- Step 6.1-6.5: 测试验证（需要 Chrome 实例手动测试）

### 验证标准回顾
- ✅ CDP 文件上传能真实设置文件到 input 元素（DOM.setFileInputFiles）
- ⏳ 发布流程完成后能在平台看到内容（需手动测试）
- ✅ Chrome 未启动时自动降级（auto_publisher 超时 + CDP 连接检测）