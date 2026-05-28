# 2026-05-28 服务自动结束问题修复

## 问题描述
Terminal#159-498 启动后端服务后，服务运行一段时间会自动结束，需要找到根因并修复。

## 根因分析

经过全面代码审查，发现以下 **5 个可能导致服务自动结束的问题**：

### 🔴 P0（最可能原因）: `uvicorn --reload` 监控 SQLite DB 文件导致频繁重启/崩溃

**位置**: `server.py:63-69`

**问题**:
- `server.py` 启动 uvicorn 时使用了 `--reload` 参数
- SQLite 数据库文件 `intent_money.db` 位于后端工作目录中
- `--reload` 使用 `watchfiles` 监控工作目录的文件变化
- **每次数据库写入都会修改 `.db` 文件**，触发 uvicorn 检测到变化并重启 worker
- 后台定时任务每 2 小时写一次 DB（snapshot_fetch），每 24 小时写一次（market_analysis, scrape_hot_videos）
- API 请求也会写 DB
- 在 Windows 上，`watchfiles` 对频繁变化的文件处理不稳定，可能导致 uvicorn 主进程崩溃
- 一旦主进程崩溃，`server.py` 中的 `backend_proc.wait()` 返回，服务完全停止

### 🟠 P1: CdpBrowser 实例未关闭导致内存泄漏

**位置**: `market_service.py:185-186`, `market_service.py:269`

**问题**:
- `scrape_and_save_hot_videos()` 和 `scrape_and_save_xhs_notes()` 创建 `CdpDouyinScraper()` / `CdpXhsScraper()` 实例
- 这些 scraper 内部创建 `CdpBrowser` 实例，持有 WebSocket 连接
- **但函数结束后从未调用 `browser.close()`**，WebSocket 连接泄漏
- 后台任务 `daily_scrape_hot_videos()` 每 24 小时调用一次，每次泄漏一个连接
- 长期运行后内存和连接数持续增长，最终可能导致 OOM 或连接耗尽

### 🟡 P2: 后台任务异常处理不完善

**位置**: `main.py:17-61`

**问题**:
- 4 个后台任务使用 `asyncio.create_task()` 创建，是 fire-and-forget 模式
- 虽然有 `try/except` 块，但缺少 `CancelledError` 处理
- 当 uvicorn --reload 重启时，旧的 event loop 被销毁，后台任务被强制取消，可能导致资源泄漏

### 🟡 P3: SQLite 数据库并发写入锁定

**位置**: `database.py:9-13`

**问题**:
- SQLite 默认在写入时锁定整个数据库文件
- 多个后台任务和 API 请求同时写入时，可能出现 `OperationalError: database is locked`
- 当前没有配置 WAL 模式（Write-Ahead Logging），WAL 模式允许读写并发

### 🟢 P4: 缺少进程级异常捕获和日志

**问题**:
- `server.py` 中 `backend_proc.wait()` 只等待进程退出，没有捕获退出原因
- 没有记录 uvicorn 的退出码和 stderr 输出
- 当服务停止时，无法从日志中判断是崩溃还是正常退出

---

## 修复实施

### 修复 1: 移除默认 `--reload`（P0）

**文件**: `server.py`

**修改内容**:
1. `start_backend()` 函数添加 `reload: bool = False` 参数
2. 默认不启用 `--reload`，如需启用需显式传入 `--reload` 参数
3. 启用时限制 `--reload-dir app/`，只监控 `app/` 目录，排除 `.db` 文件
4. 添加退出码诊断日志

```python
def start_backend(host: str, port: int, reload: bool = False) -> subprocess.Popen:
    ...
    if reload:
        cmd.extend(["--reload", "--reload-dir", "app"])
```

### 修复 2: CdpBrowser 内存泄漏（P1）

**文件**: `market_service.py`

**修改内容**:
1. 添加 `_close_scraper()` 辅助函数，安全关闭 CdpBrowser WebSocket 连接
2. 在 `scrape_and_save_xhs_notes()` 和 `scrape_and_save_hot_videos()` 的所有退出路径上调用关闭

```python
async def _close_scraper(scraper) -> None:
    if hasattr(scraper, "_browser") and hasattr(scraper._browser, "close"):
        try:
            await scraper._browser.close()
        except Exception:
            pass
```

### 修复 3: 完善后台任务异常处理（P2）

**文件**: `main.py`

**修改内容**:
1. 每个后台任务添加 `CancelledError` 处理，确保优雅退出
2. lifespan 中保存任务引用，关闭时主动取消所有任务并等待完成
3. 添加任务启动和取消的日志

```python
async def daily_market_analysis():
    while True:
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("daily_market_analysis cancelled, exiting")
            return
        # ...
```

### 修复 4: 启用 SQLite WAL 模式（P3）

**文件**: `database.py`

**修改内容**:
1. 添加 `PRAGMA journal_mode=WAL`：允许读写并发，不再锁定整个数据库
2. 添加 `PRAGMA busy_timeout=5000`：写入冲突时等待 5 秒而非立即报错

```python
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection: object, connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
```

### 修复 5: 添加诊断日志（P4）

**文件**: `server.py`

**修改内容**:
捕获 uvicorn 退出码，异常退出时打印警告

```python
backend_proc.wait()
exit_code = backend_proc.returncode
if exit_code != 0:
    print(f"[server] [WARN] 后端进程异常退出 (exit_code={exit_code})")
```

---

## 启动方式变更

### 之前（有问题）
```bash
python server.py  # 默认带 --reload，会因 DB 文件变化频繁重启
```

### 现在（稳定）
```bash
python server.py  # 不带 --reload，稳定运行
```

### 开发时热重载（可选）
```bash
python server.py --reload  # 仅监控 app/ 目录，排除 .db 文件
```

---

## 测试验证

1. 启动服务：`uv run uvicorn app.main:app --host=127.0.0.1 --port=9091`
2. health 接口持续正常返回
3. 服务运行超过 2 分钟无重启、无异常日志
4. 内存使用稳定，无泄漏迹象

---

## 相关文件

- `intent-money/backend/server.py`
- `intent-money/backend/app/main.py`
- `intent-money/backend/app/database.py`
- `intent-money/backend/app/services/market_service.py`
