"""Intent Money OS - 后端启动脚本

使用方法:
    python server.py              # 启动后端
    python server.py --api-mode   # API 模式（同默认模式）
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 9090


def start_backend(host: str, port: int, reload: bool = False) -> subprocess.Popen:
    """启动 FastAPI 后端."""
    print(f"[server] 启动后端 http://{host}:{port}")
    uv_path = _find_uv()
    if uv_path:
        cmd = [
            "uv", "run", "uvicorn",
            "app.main:app",
            f"--host={host}",
            f"--port={port}",
        ]
    else:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            f"--host={host}",
            f"--port={port}",
        ]
    if reload:
        cmd.extend(["--reload", "--reload-dir", "app"])
    proc = subprocess.Popen(cmd, cwd=str(BACKEND_DIR))
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
    parser = argparse.ArgumentParser(description="Intent Money OS 后端启动")
    parser.add_argument("--api-mode", action="store_true", help="API 模式（同默认模式）")
    parser.add_argument("--port", type=int, default=BACKEND_PORT, help=f"后端端口 (默认 {BACKEND_PORT})")
    parser.add_argument("--reload", action="store_true", help="启用热重载（仅监控 app/ 目录，排除 .db 文件）")
    args = parser.parse_args()

    backend_proc = None

    try:
        backend_proc = start_backend(BACKEND_HOST, args.port, reload=args.reload)
        print(f"\n[server] [OK] 后端已启动: http://{BACKEND_HOST}:{args.port}")
        if args.reload:
            print("[server] 热重载已启用（仅监控 app/ 目录）")
        print("[server] 按 Ctrl+C 停止\n")

        backend_proc.wait()
        exit_code = backend_proc.returncode
        if exit_code != 0:
            print(f"[server] [WARN] 后端进程异常退出 (exit_code={exit_code})")

    except KeyboardInterrupt:
        print("\n[server] 正在停止...")
    finally:
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        print("[server] 已停止")


if __name__ == "__main__":
    main()
