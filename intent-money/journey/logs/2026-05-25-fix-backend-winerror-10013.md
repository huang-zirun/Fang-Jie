# 后端 WinError 10013 启动失败修复 - 2026-05-25

## 现象

每次运行 `uv run python server.py`，后端启动后立即报错：
```
[Backend] ERROR:    [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字。
```
前端能启动，但后端子进程异常退出 (code: 1)，整个服务无法使用。

## 排查过程

1. **排除端口占用**：`netstat -ano | findstr :9090` 发现 PID 53388 的 python.exe 占用端口，kill 后问题依旧
2. **排除 Hyper-V 端口保留**：`netsh int ipv4 show excludedportrange protocol=tcp` 确认 9090 不在保留范围内
3. **直接启动测试**：`uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 9090` 单独运行正常，无 10013
4. **定位根因**：问题出在 `server.py` 的 `--reload` 模式 —— 不带 `--reload-dir` 时，WatchFiles 监听整个 `backend/` 目录（含 `.venv`、`*.db`、`cookies/`），在 Windows 上文件句柄与 socket bind 产生竞争，触发 10013

## 修复

### 修复 1：限制 reload 监听范围（`server.py` 第 121 行）

```python
# 修复前
"--reload", "--host", "127.0.0.1", "--port", "9090"

# 修复后
"--reload", "--reload-dir", "app",
"--host", "127.0.0.1", "--port", "9090"
```

只监听 `app/` 目录，避免 WatchFiles 对 `.venv` / `*.db` 等文件开句柄干扰 socket bind。

### 修复 2：添加真实启动探针（`server.py` 第 141-156 行）

用 `socket.create_connection` 轮询 `127.0.0.1:9090` 最多 15 秒，端口真正监听后才打印"后端服务已启动"。若端口从未打开，明确报错并退出，不再出现"已启动"后 3 秒静默崩溃的现象。

```python
import socket
backend_ready = False
for _ in range(30):
    if backend_proc.poll() is not None:
        break
    try:
        with socket.create_connection(("127.0.0.1", 9090), timeout=0.5):
            backend_ready = True
            break
    except OSError:
        time.sleep(0.5)

if not backend_ready:
    log("后端服务启动失败，请检查端口 9090 是否被占用", Colors.RED)
    cleanup()
```

## 验证

- `uv run python server.py` → 后端正常监听 9090，无 10013
- `netstat -ano | findstr :9090` → `TCP 127.0.0.1:9090 LISTENING`
- 前端 + 后端同时启动，不再出现"子进程异常退出 (code: 1)"

## 教训

- Windows 上 Python 子进程 + `--reload` + 大目录监听 → 容易触发 WinError 10013
- 始终用 `--reload-dir` 限制监听范围，不要监听含 `.venv` / 数据库文件的目录
- 启动脚本的"已启动"应该基于端口探针，而非固定 sleep
