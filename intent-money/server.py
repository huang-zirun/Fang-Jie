#!/usr/bin/env python3
"""
Intent Money OS - 一键启动脚本
同时启动 Chrome CDP + 后端服务 + 前端开发服务器

使用方法:
    python server.py              # 启动 Chrome CDP + 前后端（默认）
    python server.py --no-chrome  # 仅启动前后端（CDP 已手动启动）
    python server.py --api-mode   # API 模式（不依赖 Chrome，使用原始爬虫）
    python server.py --reload     # 启用后端热重载
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'

def log(msg, color=Colors.GREEN):
    print(f"{color}[Intent Money]{Colors.END} {msg}")

# 配置
ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 9090

processes = []
threads = []

def check_command(cmd):
    """检查命令是否可用"""
    try:
        if sys.platform == "win32":
            if not cmd.endswith(".cmd") and not cmd.endswith(".exe"):
                for ext in [".exe", ".cmd", ""]:
                    try:
                        subprocess.run([cmd + ext, "--version"], capture_output=True, check=True, shell=True)
                        return True
                    except:
                        continue
                return False
        subprocess.run([cmd, "--version"], capture_output=True, check=True, shell=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_cmd(name):
    """获取命令（Windows 兼容）"""
    if sys.platform == "win32":
        if name == "npm":
            return "npm.cmd"
        elif name == "uv":
            return "uv.exe"
    return name

def stream_output(proc, prefix, color):
    """读取并输出子进程日志"""
    try:
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"{color}{prefix}{Colors.END} {line}", end="")
    except:
        pass

def check_cdp_available() -> bool:
    """检查 Chrome CDP 端口是否已监听"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", CDP_PORT)) == 0

def wait_cdp_ready(timeout: float = 10.0) -> bool:
    """等待 Chrome CDP 就绪"""
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", CDP_PORT)) == 0:
                return True
        time.sleep(0.5)
    return False

def find_chrome() -> str | None:
    """查找 Chrome 可执行文件路径"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    return None

def start_chrome(cdp_port: int) -> subprocess.Popen:
    """启动 Chrome 并开启远程调试端口"""
    chrome_path = find_chrome()
    if not chrome_path:
        raise FileNotFoundError("未找到 Chrome，请确保已安装 Google Chrome")

    user_data_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "intent-money-chrome")
    cmd = [
        chrome_path,
        f"--remote-debugging-port={cdp_port}",
        f"--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    log(f"启动 Chrome CDP (port={cdp_port})...", Colors.CYAN)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def cleanup(signum=None, frame=None):
    """清理所有子进程"""
    log("正在停止所有服务...", Colors.YELLOW)
    for p in processes:
        try:
            if p.poll() is None:
                p.terminate()
                p.wait(timeout=5)
        except:
            try:
                p.kill()
            except:
                pass
    log("已退出")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Intent Money OS 一键启动")
    parser.add_argument("--no-chrome", action="store_true", help="跳过启动 Chrome（CDP 已手动启动）")
    parser.add_argument("--api-mode", action="store_true", help="API 模式（不依赖 Chrome，使用原始爬虫）")
    parser.add_argument("--port", type=int, default=BACKEND_PORT, help=f"后端端口 (默认 {BACKEND_PORT})")
    parser.add_argument("--reload", action="store_true", help="启用后端热重载（仅监控 app/ 目录）")
    args = parser.parse_args()

    log("正在启动 Intent Money OS...")
    log(f"项目目录: {ROOT_DIR}")

    # 检查环境
    if not check_command("uv"):
        log("未找到 uv，请先安装: https://github.com/astral-sh/uv", Colors.RED)
        sys.exit(1)

    if not check_command("npm"):
        log("未找到 npm，请先安装 Node.js", Colors.RED)
        sys.exit(1)

    # 检查 .env 文件
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        log("未找到 .env 文件，正在创建模板...", Colors.YELLOW)
        env_content = """# Intent Money OS - 环境配置
DATABASE_URL=sqlite+aiosqlite:///./intent_money.db
SECRET_KEY=change-me-in-production
AI_API_KEY=your_openrouter_api_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=deepseek/deepseek-chat-v3-0324:free
ENV=development
CDP_ENABLED=true
CDP_DEBUG_HOST=127.0.0.1
CDP_DEBUG_PORT=9222
"""
        env_file.write_text(env_content, encoding="utf-8")
        log("已创建 .env 模板，请编辑并填入 AI_API_KEY", Colors.YELLOW)

    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    chrome_proc = None
    backend_proc = None
    frontend_proc = None

    try:
        # ========== 1. 启动 Chrome CDP ==========
        if args.api_mode:
            os.environ["CDP_ENABLED"] = "false"
            log("运行模式: API（原始爬虫，不依赖 Chrome）", Colors.CYAN)
        else:
            os.environ["CDP_ENABLED"] = "true"

            if check_cdp_available():
                log(f"Chrome CDP 已在端口 {CDP_PORT} 运行", Colors.CYAN)
            elif not args.no_chrome:
                try:
                    chrome_proc = start_chrome(CDP_PORT)
                    processes.append(chrome_proc)
                    if not wait_cdp_ready(timeout=10.0):
                        log("Chrome CDP 启动失败，请手动启动 Chrome 后重试", Colors.RED)
                        chrome_path = find_chrome() or CHROME_PATH
                        log(f"手动命令: {chrome_path} --remote-debugging-port={CDP_PORT}", Colors.YELLOW)
                        cleanup()
                    log(f"Chrome CDP 已就绪 (pid={chrome_proc.pid})", Colors.CYAN)
                except FileNotFoundError as e:
                    log(str(e), Colors.RED)
                    cleanup()
            else:
                log(f"端口 {CDP_PORT} 未监听，请先启动 Chrome CDP", Colors.RED)
                cleanup()

        # ========== 2. 启动后端 ==========
        log("启动后端服务 (FastAPI)...")

        # 设置环境变量
        env = os.environ.copy()
        env["CDP_ENABLED"] = os.environ.get("CDP_ENABLED", "true")

        uv_cmd = get_cmd("uv")
        backend_cmd = [
            uv_cmd, "run", "uvicorn", "app.main:app",
            "--host", BACKEND_HOST,
            "--port", str(args.port),
        ]
        if args.reload:
            backend_cmd.extend(["--reload", "--reload-dir", "app"])

        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        processes.append(backend_proc)

        # 启动后端日志线程
        backend_thread = threading.Thread(target=stream_output, args=(backend_proc, "[Backend]", Colors.BLUE))
        backend_thread.daemon = True
        backend_thread.start()
        threads.append(backend_thread)

        # 等待后端真正监听端口（最多 15 秒）
        backend_ready = False
        for _ in range(30):
            if backend_proc.poll() is not None:
                break
            try:
                with socket.create_connection((BACKEND_HOST, args.port), timeout=0.5):
                    backend_ready = True
                    break
            except OSError:
                time.sleep(0.5)

        if not backend_ready:
            log(f"后端服务启动失败，请检查端口 {args.port} 是否被占用", Colors.RED)
            cleanup()

        log(f"后端服务已启动: http://{BACKEND_HOST}:{args.port}")
        log(f"API 文档: http://{BACKEND_HOST}:{args.port}/docs")

        # ========== 3. 启动前端 ==========
        log("启动前端服务 (Vue 3)...")
        npm_cmd = get_cmd("npm")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        processes.append(frontend_proc)

        # 启动前端日志线程
        frontend_thread = threading.Thread(target=stream_output, args=(frontend_proc, "[Frontend]", Colors.YELLOW))
        frontend_thread.daemon = True
        frontend_thread.start()
        threads.append(frontend_thread)

        # ========== 启动完成 ==========
        log("")
        log("=" * 50)
        log("所有服务已启动！")
        log("=" * 50)
        log("")
        log("访问地址:")
        log("  - 前端: http://localhost:5173")
        log(f"  - 后端: http://{BACKEND_HOST}:{args.port}")
        log(f"  - API文档: http://{BACKEND_HOST}:{args.port}/docs")
        if not args.api_mode:
            log(f"  - Chrome CDP: http://127.0.0.1:{CDP_PORT}")
        log("")
        log("按 Ctrl+C 停止所有服务")
        log("")

        # 主循环：检查进程状态
        while True:
            for p in processes:
                if p.poll() is not None:
                    log(f"子进程异常退出 (code: {p.returncode})", Colors.RED)
                    cleanup()
            time.sleep(1)

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        log(f"错误: {e}", Colors.RED)
        cleanup()

if __name__ == "__main__":
    main()
