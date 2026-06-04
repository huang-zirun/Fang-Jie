#!/bin/sh
set -e
export PYTHONPATH=/app

# 确保数据目录存在且有正确权限
mkdir -p /app/data

# 输出诊断信息
echo "=== Intent Money OS 启动诊断 ==="
echo "DATABASE_URL: ${DATABASE_URL:-未设置}"
echo "ENV: ${ENV:-未设置}"
echo "DEV_MODE: ${DEV_MODE:-未设置}"
echo "数据目录内容:"
ls -la /app/data 2>/dev/null || echo "  无法访问"
echo "================================"

# 检查数据库迁移状态
# 问题背景：如果数据库是通过 Base.metadata.create_all() 创建的，
# 它不会有 alembic_version 表，导致 alembic upgrade head 从头开始，
# 而 "CREATE TABLE" 会因表已存在而失败。
echo "正在检查数据库迁移状态..."

# 从 DATABASE_URL 提取数据库文件路径
DB_PATH=""
case "$DATABASE_URL" in
    sqlite+aiosqlite:////*)
        # 绝对路径: sqlite+aiosqlite:////app/data/intent_money.db -> /app/data/intent_money.db
        DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite+aiosqlite:////||')
        ;;
    sqlite+aiosqlite:///./intent_money.db)
        # 相对路径
        DB_PATH="/app/intent_money.db"
        ;;
    sqlite+aiosqlite:///*)
        # 其他绝对路径
        DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite+aiosqlite:///||')
        ;;
    *)
        DB_PATH="/app/data/intent_money.db"
        ;;
esac

echo "数据库文件路径: $DB_PATH"

# 检查数据库文件是否存在
if [ -f "$DB_PATH" ]; then
    echo "✅ 数据库文件存在"
    
    # 检查是否已有 alembic_version 记录
    # 使用 uv run python 执行，确保在正确的环境中
    HAS_VERSION=$(uv run python -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    rows = conn.execute('SELECT version_num FROM alembic_version').fetchall()
    conn.close()
    if rows:
        print('yes')
    else:
        print('no')
except Exception:
    print('no')
" 2>/dev/null || echo "no")
    
    echo "alembic 版本记录: $HAS_VERSION"
    
    if [ "$HAS_VERSION" = "yes" ]; then
        echo "📋 数据库已有 alembic 版本记录，执行增量迁移..."
        uv run alembic upgrade head
        echo "✅ 数据库迁移完成"
    else
        # 检查是否有其他表（说明数据库是通过 create_all 创建的）
        HAS_TABLES=$(uv run python -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'\").fetchall()
    conn.close()
    if tables:
        print('yes')
    else:
        print('no')
except Exception:
    print('no')
" 2>/dev/null || echo "no")
        
        echo "已有数据表: $HAS_TABLES"
        
        if [ "$HAS_TABLES" = "yes" ]; then
            echo "⚠️  数据库已有表但缺少 alembic 版本记录"
            echo "   正在标记数据库到最新迁移版本（跳过已执行的迁移）..."
            uv run alembic stamp head
            echo "✅ 数据库版本标记完成"
        else
            echo "🆕 空数据库，执行完整迁移..."
            uv run alembic upgrade head
            echo "✅ 数据库迁移完成"
        fi
    fi
else
    echo "🆕 数据库文件不存在，执行完整迁移..."
    uv run alembic upgrade head
    echo "✅ 数据库迁移完成"
fi

# 启动应用
echo "正在启动应用..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
