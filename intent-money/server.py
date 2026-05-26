#!/usr/bin/env python3
"""
Intent Money OS - 一键启动脚本
同时启动后端服务和前端开发服务器
"""

import subprocess
import sys
import os
import signal
import time
import threading
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def log(msg, color=Colors.GREEN):
    print(f"{color}[Intent Money]{Colors.END} {msg}")

def check_command(cmd):
    """检查命令是否可用"""
    try:
        # Windows 下尝试 .cmd 或 .exe 后缀
        if sys.platform == "win32":
            if not cmd.endswith(".cmd") and not cmd.endswith(".exe"):
                # 尝试各种后缀
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

def main():
    # 获取项目根目录
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"

    log("正在启动 Intent Money OS...")
    log(f"项目目录: {root_dir}")

    # 检查环境
    if not check_command("uv"):
        log("未找到 uv，请先安装: https://github.com/astral-sh/uv", Colors.RED)
        sys.exit(1)

    if not check_command("npm"):
        log("未找到 npm，请先安装 Node.js", Colors.RED)
        sys.exit(1)

    # 检查 .env 文件
    env_file = backend_dir / ".env"
    if not env_file.exists():
        log("未找到 .env 文件，正在创建模板...", Colors.YELLOW)
        env_content = """# Intent Money OS - 环境配置
DATABASE_URL=sqlite+aiosqlite:///./intent_money.db
SECRET_KEY=change-me-in-production
AI_API_KEY=your_openrouter_api_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=deepseek/deepseek-chat-v3-0324:free
ENV=development
"""
        env_file.write_text(env_content, encoding="utf-8")
        log("已创建 .env 模板，请编辑并填入 AI_API_KEY", Colors.YELLOW)

    processes = []
    threads = []

    def cleanup(signum=None, frame=None):
        """清理所有子进程"""
        log("正在停止所有服务...", Colors.YELLOW)
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except:
                p.kill()
        log("已退出")
        sys.exit(0)

    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # 启动后端
        log("启动后端服务 (FastAPI)...")
        uv_cmd = get_cmd("uv")
        backend_cmd = [
            uv_cmd, "run", "uvicorn", "app.main:app",
            "--reload", "--reload-dir", "app",
            "--host", "127.0.0.1", "--port", "9090"
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        processes.append(backend_proc)

        # 启动后端日志线程
        backend_thread = threading.Thread(target=stream_output, args=(backend_proc, "[Backend]", Colors.BLUE))
        backend_thread.daemon = True
        backend_thread.start()
        threads.append(backend_thread)

        # 等待后端真正监听端口（最多 15 秒），避免在绑定失败时误报"已启动"
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

        log("后端服务已启动: http://127.0.0.1:9090")
        log("API 文档: http://127.0.0.1:9090/docs")

        # 启动前端
        log("启动前端服务 (Vue 3)...")
        npm_cmd = get_cmd("npm")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir,
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

        log("")
        log("=" * 50)
        log("所有服务已启动！")
        log("=" * 50)
        log("")
        log("访问地址:")
        log("  - 前端: http://localhost:5173")
        log("  - 后端: http://127.0.0.1:9090")
        log("  - API文档: http://127.0.0.1:9090/docs")
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
