"""数据库迁移状态检查和自动修复工具。

在 entrypoint.sh 中调用，用于检测数据库是否已有表但缺少 alembic 版本记录，
如果是，则自动执行 alembic stamp head 标记版本，避免 "table already exists" 错误。

同时也会验证数据库结构是否与当前 model 一致，如果不一致会修复。
"""

import os
import sqlite3
import subprocess
import sys


def get_db_path() -> str:
    """从 DATABASE_URL 环境变量提取 SQLite 数据库文件路径。"""
    db_url = os.environ.get("DATABASE_URL", "")
    prefix = "sqlite+aiosqlite:///"
    if db_url.startswith(prefix):
        path_part = db_url[len(prefix):]
        if path_part.startswith("/"):
            return path_part
        else:
            return os.path.join("/app", path_part)
    return "/app/data/intent_money.db"


def check_db_state(db_path: str) -> str:
    """检查数据库状态。

    Returns:
        "no_db" - 数据库文件不存在
        "empty_db" - 数据库存在但没有用户表
        "has_version" - 数据库有 alembic 版本记录
        "stamp_needed" - 数据库有表但没有 alembic 版本记录
        "version_mismatch" - 有版本记录但结构与版本不一致
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
                    # 有版本记录，但需要验证结构是否一致
                    if not _validate_schema(conn):
                        return "version_mismatch"
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


def _validate_schema(conn: sqlite3.Connection) -> bool:
    """验证数据库结构是否与当前 model 要求一致。

    检查关键列是否存在，如果缺少说明 alembic stamp 与实际结构不匹配。
    """
    checks = [
        ("platforms", "created_at"),
        ("users", "is_anonymous"),
        ("users", "updated_at"),
        ("intents", "sort_order"),
    ]

    for table, column in checks:
        try:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_names = {c[1] for c in cols}
            if column not in col_names:
                print(f"   ⚠️  结构不匹配: {table}.{column} 缺失")
                return False
        except Exception as e:
            print(f"   ⚠️  检查 {table} 时出错: {e}")
            return False

    return True


def get_db_columns(db_path: str, table_name: str) -> set[str]:
    """获取数据库表中已有的列名集合。"""
    try:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}
        finally:
            conn.close()
    except Exception:
        return set()


def determine_stamp_version(db_path: str) -> str:
    """根据数据库实际表结构确定应该 stamp 到哪个版本。

    迁移链: 000000000000 -> 6447982821b9 -> a1b2c3d4e5f6

    6447982821b9 添加了 user_platform_accounts 表
    a1b2c3d4e5f6 添加了:
      - users: is_anonymous, updated_at (替代 is_active)
      - intents: sort_order
      - platforms: created_at
    """
    try:
        conn = sqlite3.connect(db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        conn.close()
    except Exception:
        return "000000000000"

    has_user_platform_accounts = "user_platform_accounts" in tables

    # 检查最新迁移的列是否存在
    users_cols = get_db_columns(db_path, "users")
    platforms_cols = get_db_columns(db_path, "platforms")

    has_is_anonymous = "is_anonymous" in users_cols
    has_platforms_created_at = "created_at" in platforms_cols

    if has_user_platform_accounts and has_is_anonymous and has_platforms_created_at:
        return "head"
    elif has_user_platform_accounts:
        return "6447982821b9"
    else:
        return "000000000000"


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
        print("📋 数据库已有版本记录且结构一致，执行增量迁移...")
        rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])
        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")

    elif state == "version_mismatch":
        print("⚠️  数据库有版本记录但结构与 model 不一致！")
        print("   这通常是因为 alembic stamp 与实际表结构不匹配")
        print("   正在根据实际表结构重新标记版本...")

        # 先删除 alembic_version 记录
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("DELETE FROM alembic_version")
            conn.commit()
            conn.close()
            print("   ✅ 已清除旧的 alembic 版本记录")
        except Exception as e:
            print(f"   ❌ 清除版本记录失败: {e}")
            sys.exit(1)

        # 根据实际结构确定版本
        stamp_version = determine_stamp_version(db_path)
        print(f"   数据库实际结构对应版本: {stamp_version}")

        if stamp_version == "head":
            print("   数据库结构与最新迁移一致，重新标记...")
            rc = run_cmd(["uv", "run", "alembic", "stamp", "head"])
        else:
            print(f"   先标记到版本 {stamp_version}，再执行增量迁移...")
            rc = run_cmd(["uv", "run", "alembic", "stamp", stamp_version])
            if rc != 0:
                print("❌ 版本标记失败")
                sys.exit(rc)
            print(f"✅ 已标记到版本 {stamp_version}")
            print("   执行增量迁移...")
            rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])

        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")

    elif state == "stamp_needed":
        print("⚠️  数据库已有表但缺少 alembic 版本记录")

        # 根据数据库实际结构确定应该 stamp 到哪个版本
        stamp_version = determine_stamp_version(db_path)
        print(f"   数据库结构与迁移版本对应: {stamp_version}")

        if stamp_version == "head":
            print("   数据库结构与最新迁移一致，直接标记...")
            rc = run_cmd(["uv", "run", "alembic", "stamp", "head"])
        else:
            print(f"   先标记到版本 {stamp_version}，再执行增量迁移...")
            rc = run_cmd(["uv", "run", "alembic", "stamp", stamp_version])
            if rc != 0:
                print("❌ 版本标记失败")
                sys.exit(rc)
            print(f"✅ 已标记到版本 {stamp_version}")
            print("   执行增量迁移...")
            rc = run_cmd(["uv", "run", "alembic", "upgrade", "head"])

        if rc != 0:
            print("❌ 数据库迁移失败")
            sys.exit(rc)
        print("✅ 数据库迁移完成")


if __name__ == "__main__":
    main()
