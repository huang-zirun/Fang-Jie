"""Intent Money OS - 一键启动脚本（CDP 模式）

使用方法:
    python server.py              # 启动 Chrome CDP + 后端
    python server.py --no-chrome  # 仅启动后端（CDP 已手动启动）
    python server.py --api-mode   # API 模式（不依赖 Chrome）
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 9090


def check_cdp_available() -> bool:
    """检查 Chrome CDP 端口是否已监听."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", CDP_PORT)) == 0


def wait_cdp_ready(timeout: float = 10.0) -> bool:
    """等待 Chrome CDP 就绪."""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", CDP_PORT)) == 0:
                return True
        time.sleep(0.5)
    return False


def start_chrome(cdp_port: int) -> subprocess.Popen:
    """启动 Chrome 并开启远程调试端口."""
    user_data_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "intent-money-chrome")
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={cdp_port}",
        f"--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={user-data_dir}",
    ]
    print(f"[server] 启动 Chrome CDP (port={cdp_port})...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def start_backend(host: str, port: int) -> subprocess.Popen:
    """启动 FastAPI 后端."""
    env = os.environ.copy()
    env["CDP_ENABLED"] = "true"
    print(f"[server] 启动后端 http://{host}:{port}")
    # 优先使用 uv run，回退到 python -m uvicorn
    uv_path = _find_uv()
    if uv_path:
        cmd = [
            "uv", "run", "uvicorn",
            "app.main:app",
            f"--host={host}",
            f"--port={port}",
            "--reload",
        ]
    else:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            f"--host={host}",
            f"--port={port}",
            "--reload",
        ]
    proc = subprocess.Popen(cmd, cwd=str(BACKEND_DIR), env=env)
    return proc


def _find_uv() -> str | None:
    """查找 uv 可执行文件路径."""
    for path in ["uv", "uv.exe"]:
        try:
            subprocess.run([path, "--version"], capture_output=True, timeout=3)
            return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def main():
    parser = argparse.ArgumentParser(description="Intent Money OS 一键启动")
    parser.add_argument("--no-chrome", action="store_true", help="跳过启动 Chrome（CDP 已手动启动）")
    parser.add_argument("--api-mode", action="store_true", help="API 模式（不依赖 Chrome）")
    parser.add_argument("--port", type=int, default=BACKEND_PORT, help=f"后端端口 (默认 {BACKEND_PORT})")
    args = parser.parse_args()

    chrome_proc = None
    backend_proc = None

    try:
        if args.api_mode:
            # API 模式：不依赖 Chrome
            os.environ["CDP_ENABLED"] = "false"
            print("[server] 运行模式: API（原始爬虫）")
        else:
            # CDP 模式
            os.environ["CDP_ENABLED"] = "true"

            if check_cdp_available():
                print(f"[server] Chrome CDP 已在端口 {CDP_PORT} 运行")
            elif not args.no_chrome:
                chrome_proc = start_chrome(CDP_PORT)
                if not wait_cdp_ready(timeout=10.0):
                    print("[server] [FAIL] Chrome CDP 启动失败，请手动启动 Chrome 后重试")
                    print(f"[server] 手动命令: {CHROME_PATH} --remote-debugging-port={CDP_PORT}")
                    sys.exit(1)
                print(f"[server] [OK] Chrome CDP 已就绪 (pid={chrome_proc.pid})")
            else:
                print(f"[server] [FAIL] 端口 {CDP_PORT} 未监听，请先启动 Chrome CDP")
                sys.exit(1)

        backend_proc = start_backend(BACKEND_HOST, args.port)
        print(f"\n[server] [OK] 后端已启动: http://{BACKEND_HOST}:{args.port}")
        print("[server] 按 Ctrl+C 停止\n")

        # 等待后端进程
        backend_proc.wait()

    except KeyboardInterrupt:
        print("\n[server] 正在停止...")
    finally:
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        if chrome_proc and chrome_proc.poll() is None:
            chrome_proc.terminate()
            chrome_proc.wait(timeout=5)
        print("[server] 已停止")


if __name__ == "__main__":
    main()
