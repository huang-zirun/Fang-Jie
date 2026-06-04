"""数据库迁移状态检查和自动修复工具。

在 entrypoint.sh 中调用，用于检测数据库是否已有表但缺少 alembic 版本记录，
如果是，则自动执行 alembic stamp head 标记版本，避免 "table already exists" 错误。
"""

import os
import sqlite3
import subprocess
import sys


def get_db_path() -> str:
    """从 DATABASE_URL 环境变量提取 SQLite 数据库文件路径。

    SQLAlchemy aiosqlite URL 格式说明：
    - 绝对路径: sqlite+aiosqlite:////app/data/intent_money.db
      (:// 是协议分隔符，/ 是 SQLite 绝对路径前缀，/app/data/... 是实际路径)
    - 相对路径: sqlite+aiosqlite:///./intent_money.db
      (三个斜杠 + 点 + 斜杠 表示相对于当前工作目录)
    """
    db_url = os.environ.get("DATABASE_URL", "")

    # 去掉协议前缀，提取路径部分
    # sqlite+aiosqlite:/// 后面的部分就是路径
    # 关键：用 urlparse 或者简单的字符串处理
    prefix = "sqlite+aiosqlite:///"
    if db_url.startswith(prefix):
        path_part = db_url[len(prefix):]
        # path_part 可能是:
        #   /app/data/intent_money.db (绝对路径，第一个字符是 /)
        #   ./intent_money.db (相对路径)
        #   intent_money.db (相对路径，无 ./)
        if path_part.startswith("/"):
            # 绝对路径
            return path_part
        else:
            # 相对路径，基于 /app 工作目录
            return os.path.join("/app", path_part)

    # 回退默认值
    return "/app/data/intent_money.db"


def check_db_state(db_path: str) -> str:
    """检查数据库状态。

    Returns:
        "no_db" - 数据库文件不存在
        "empty_db" - 数据库存在但没有用户表
        "has_version" - 数据库有 alembic 版本记录
        "stamp_needed" - 数据库有表但没有 alembic 版本记录
    """
    if not os.path.exists(db_path):
        return "no_db"

    try:
        conn = sqlite3.connect(db_path)
        try:
            # 检查 alembic_version 表
            result = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()

            if result[0] > 0:
                version = conn.execute("SELECT version_num FROM alembic_version").fetchall()
                if version:
                    return "has_version"

            # 检查是否有用户表
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'"
            ).fetchall()

            if tables:
                return "stamp_needed"
            else:
                return "empty_db"
        finally:
            conn.close()
    except Exception as e:
        print(f"⚠️  检查数据库时出错: {e}")
        return "empty_db"


def run_cmd(cmd: list[str]) -> int:
    """运行命令并实时输出。"""
    print(f"   执行: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    print("正在检查数据库迁移状态...")

    db_path = get_db_path()
    print(f"   数据库路径: {db_path}")

    state = check_db_state(db_path)
    print(f"   数据库状态: {state}")

    if state == "no_db":
        print("🆕 数据库文件不存在，执行完整迁移...")
        rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])
        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")

    elif state == "empty_db":
        print("🆕 空数据库，执行完整迁移...")
        rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])
        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")

    elif state == "has_version":
        print("📋 数据库已有版本记录，执行增量迁移...")
        rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])
        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")

    elif state == "stamp_needed":
        print("⚠️  数据库已有表但缺少 alembic 版本记录")
        print("   正在标记数据库到最新版本（跳过已执行的迁移）...")
        rc = run_cmd(["uv", "run", "alembic", "stamp", "head"])
        if rc != 0:
            print("❌ 版本标记失败")
            sys.exit(rc)
        print("✅ 数据库版本标记完成")


if __name__ == "__main__":
    main()
