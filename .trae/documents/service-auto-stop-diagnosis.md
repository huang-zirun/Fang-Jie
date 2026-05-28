# 服务自动结束问题排查与修复计划

## 问题描述
Terminal#159-498 启动后端服务后，服务运行一段时间会自动结束，需要找到根因并修复。

## 根因分析

经过全面代码审查，发现以下 **5 个可能导致服务自动结束的问题**，按可能性排序：

---

### 🔴 P0: `uvicorn --reload` 监控 SQLite DB 文件导致频繁重启/崩溃

**位置**: [server.py:63-69](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/server.py#L63-L69)

**问题**:
- `server.py` 启动 uvicorn 时使用了 `--reload` 参数
- SQLite 数据库文件 `intent_money.db` 位于后端工作目录中
- `--reload` 使用 `watchfiles` 监控工作目录的文件变化
- **每次数据库写入都会修改 `.db` 文件**，触发 uvicorn 检测到变化并重启 worker
- 后台定时任务每 2 小时写一次 DB（snapshot_fetch），每 24 小时写一次（market_analysis, scrape_hot_videos）
- API 请求也会写 DB
- 在 Windows 上，`watchfiles` 对频繁变化的文件处理不稳定，可能导致 uvicorn 主进程崩溃
- 一旦主进程崩溃，`server.py` 中的 `backend_proc.wait()` 返回，服务完全停止

**修复方案**:
1. 移除 `--reload` 参数（生产环境不应使用）
2. 或添加 `--reload-exclude "*.db"` 排除数据库文件
3. 或添加 `--reload-dir app/` 只监控 app 目录

---

### 🟠 P1: CdpBrowser 实例未关闭导致内存泄漏

**位置**: [market_service.py:185-186](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/market_service.py#L185-L186), [market_service.py:269](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/services/market_service.py#L269)

**问题**:
- `scrape_and_save_hot_videos()` 和 `scrape_and_save_xhs_notes()` 创建 `CdpDouyinScraper()` / `CdpXhsScraper()` 实例
- 这些 scraper 内部创建 `CdpBrowser` 实例，持有 WebSocket 连接
- **但函数结束后从未调用 `browser.close()`**，WebSocket 连接泄漏
- 后台任务 `daily_scrape_hot_videos()` 每 24 小时调用一次，每次泄漏一个连接
- 长期运行后内存和连接数持续增长，最终可能导致 OOM 或连接耗尽

**修复方案**:
- 在 `scrape_and_save_hot_videos()` 和 `scrape_and_save_xhs_notes()` 中使用 `try/finally` 确保 browser 关闭
- 或让 scraper 实现 async context manager

---

### 🟡 P2: 后台任务异常处理不完善

**位置**: [main.py:17-61](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/main.py#L17-L61)

**问题**:
- 4 个后台任务使用 `asyncio.create_task()` 创建，是 fire-and-forget 模式
- 虽然有 `try/except` 块，但：
  - `daily_scrape_hot_videos()` 调用的 `scrape_and_save_hot_videos()` 可能抛出未预期的异常
  - `periodic_snapshot_fetch()` 中的 `scheduled_snapshot_fetch()` 创建 browser 但如果异常发生在 `finally` 之前，browser 不会被关闭
  - 如果 `asyncio.sleep()` 被取消（如 uvicorn 重启时），会抛出 `CancelledError`，当前代码没有处理
- 当 uvicorn --reload 重启时，旧的 event loop 被销毁，后台任务被强制取消，可能导致资源泄漏

**修复方案**:
- 为每个后台任务添加 `CancelledError` 处理
- 在 lifespan 的 yield 之后添加清理逻辑
- 添加任务引用以便在关闭时取消

---

### 🟡 P3: SQLite 数据库并发写入锁定

**位置**: [database.py:9-13](file:///e:/系统文件夹/Desktop/Channing/Fang-Jie/intent-money/backend/app/database.py#L9-L13)

**问题**:
- SQLite 默认在写入时锁定整个数据库文件
- 多个后台任务和 API 请求同时写入时，可能出现 `OperationalError: database is locked`
- 当前没有配置 WAL 模式（Write-Ahead Logging），WAL 模式允许读写并发
- `connect_args={"check_same_thread": False}` 只解决了线程检查，没有解决锁定问题

**修复方案**:
- 启用 SQLite WAL 模式：在 `_set_sqlite_pragma` 中添加 `PRAGMA journal_mode=WAL`
- 添加重试逻辑处理 `database is locked` 错误

---

### 🟢 P4: 缺少进程级异常捕获和日志

**问题**:
- `server.py` 中 `backend_proc.wait()` 只等待进程退出，没有捕获退出原因
- 没有记录 uvicorn 的退出码和 stderr 输出
- 当服务停止时，无法从日志中判断是崩溃还是正常退出

**修复方案**:
- 在 `server.py` 中捕获 uvicorn 的 stderr 和退出码
- 添加进程退出时的诊断日志

---

## 实施步骤

### 步骤 1: 修复 `--reload` 问题（P0）
1. 修改 `server.py`，移除 `--reload` 或添加 `--reload-exclude`
2. 添加 `--reload-dir app/` 限制监控范围
3. 测试：启动服务，观察是否还会自动重启

### 步骤 2: 修复 CdpBrowser 内存泄漏（P1）
1. 修改 `market_service.py` 中的 `scrape_and_save_hot_videos()` 和 `scrape_and_save_xhs_notes()`
2. 添加 `try/finally` 确保 browser 关闭
3. 测试：运行后台任务，检查 WebSocket 连接是否正确关闭

### 步骤 3: 完善后台任务异常处理（P2）
1. 修改 `main.py` 中的 4 个后台任务
2. 添加 `CancelledError` 处理和清理逻辑
3. 在 lifespan 中保存任务引用，关闭时取消
4. 测试：模拟异常情况，确认任务不会静默失败

### 步骤 4: 启用 SQLite WAL 模式（P3）
1. 修改 `database.py` 添加 `PRAGMA journal_mode=WAL`
2. 测试：并发写入，确认不再出现锁定错误

### 步骤 5: 添加诊断日志（P4）
1. 修改 `server.py` 添加退出码和 stderr 捕获
2. 测试：模拟服务停止，确认日志输出

### 步骤 6: 端到端稳定性测试
1. 启动服务，运行 30 分钟以上
2. 触发各种 API 请求和后台任务
3. 监控内存使用、WebSocket 连接数、进程状态
4. 确认服务不再自动结束

## 测试策略

1. **快速验证**: 启动服务后，手动触发数据库写入，观察是否触发 reload
2. **内存监控**: 使用 `psutil` 或任务管理器监控 Python 进程内存
3. **长时间运行**: 启动服务运行 1-2 小时，确认不再自动停止
4. **压力测试**: 并发发送 API 请求，确认 SQLite 不会锁定
