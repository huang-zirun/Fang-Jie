# CDP 自动发布实现计划

## 任务摘要
扩展 CdpBrowser 增加 DOM 域操作能力（DOM.setFileInputFiles），重写 CdpPublisher 实现真正的文件上传自动发布，复用已登录 Chrome 实例，不再依赖 social-auto-upload 或空壳 JS 注入。

## 当前问题
- `cdp_publisher.py` 文件上传是空壳（第 90-97 行注释说"CDP 无法直接设置文件路径"）
- `CdpBrowser` 只封装了 navigate/evaluate/get_page_text，缺少 DOM 域方法
- React 框架输入框的 value 设置无法触发 onChange

## 解决方案：DOM.setFileInputFiles + DOM 域扩展

---

## TODO: Step 1 - 扩展 CdpBrowser 核心 DOM 域能力
- [ ] 1.1 新增 `DOM.enable` 域启用方法（`_send_cmd("DOM.enable")`）
- [ ] 1.2 新增 `set_file_input_files(selector, file_paths)` 方法
  - 流程：DOM.getDocument → DOM.querySelector → DOM.setFileInputFiles
  - 支持 nodeId 和 backendNodeId 两种定位方式
- [ ] 1.3 新增 `wait_for_selector(selector, timeout=10)` 方法
  - 用 Runtime.evaluate 循环轮询 `document.querySelector(selector) !== null`
  - 替代硬编码 `asyncio.sleep`
- [ ] 1.4 新增 `click_element(selector)` 方法
  - DOM.getDocument → DOM.querySelector 获取 nodeId
  - 用 Runtime.evaluate 执行 `element.click()` + 事件模拟
- [ ] 1.5 新增 `fill_input(selector, value, react_compat=True)` 方法
  - React 兼容模式：使用原生 setter `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, value)` + dispatchEvent
  - 非 React 模式：直接 `el.value = value` + input/change 事件
- [ ] 1.6 新增 `fill_contenteditable(selector, text)` 方法（XHS 用 div[contenteditable]）
  - innerText 设置 + InputEvent 触发

## TODO: Step 2 - 新增 Network 域监听（上传进度 + 结果确认）
- [ ] 2.1 新增 `Network.enable` 域启用
- [ ] 2.2 新增 `listen_upload_progress()` 方法
  - 监听 `Network.requestWillBeSent` 和 `Network.loadingFinished` 事件
  - 返回上传完成/失败状态
- [ ] 2.3 新增 `listen_page_changes()` 方法
  - 监听 `DOM.childNodeInserted` 检测"发布成功"等提示文本
- [ ] 2.4 修改 `_send_cmd` 支持事件监听模式（目前只处理命令响应）
  - 需要区分"命令响应"（有 id）和"事件通知"（无 id）两类消息

## TODO: Step 3 - 重写 CdpPublisher 抖音视频发布
- [ ] 3.1 重写 `publish_douyin_video` 方法
  - navigate → creator.douyin.com/creator-micro/content/upload
  - wait_for_selector 检查登录态
  - set_file_input_files('input[type="file"]', [video_path]) ← 核心
  - wait_for_selector 等待上传完成
  - fill_input 填写标题（React 兼容模式）
  - fill_input 填写描述
  - click_element 点击发布按钮
  - listen_page_changes 确认发布结果
- [ ] 3.2 抖音登录态检测优化
  - 当前用 `get_page_text` 检查"登录"关键词 → 改用 `wait_for_selector` 检测特定元素

## TODO: Step 4 - 重写 CdpPublisher 小红书发布
- [ ] 4.1 重写 `publish_xhs_note` 图文笔记发布
  - navigate → creator.xiaohongshu.com/publish/publish
  - set_file_input_files('input[type="file"]', image_paths) ← 图片上传
  - fill_input 填写标题
  - fill_contenteditable 填写正文内容
  - click_element 点击发布
- [ ] 4.2 重写 `publish_xhs_video` 视频发布
  - navigate → creator.xiaohongshu.com/publish/publish?source=video
  - set_file_input_files 上传视频文件
  - fill_input/fill_contenteditable 填写标题和描述
  - click_element 点击发布

## TODO: Step 5 - 修改 auto_publisher.py 优先级策略
- [ ] 5.1 当前逻辑：CDP 优先 → sau 降级 → 手动确认
  - 确认 `auto_publisher.py` 调用链正确，CDP 文件上传不再是空壳后优先级不变
- [ ] 5.2 添加 CDP 发布超时保护（60秒超时自动降级）
- [ ] 5.3 添加发布结果日志记录（成功/失败/降级原因）

## TODO: Step 6 - 测试验证
- [ ] 6.1 单元测试 CdpBrowser 新方法（mock websockets）
- [ ] 6.2 手动测试抖音视频发布流程
- [ ] 6.3 手动测试小红书图文+视频发布流程
- [ ] 6.4 测试降级场景（Chrome 未启动 → sau 降级 → 手动确认）
- [ ] 6.5 测试 React 输入框兼容性

## 验证标准
- CDP 文件上传能真实设置文件到 input 元素（不再返回"无法设置"）
- 发布流程完成后能在平台看到内容（或至少上传成功）
- Chrome 未启动时自动降级到 sau/手动，不抛异常
- 本次变更需要更新到jounery系统