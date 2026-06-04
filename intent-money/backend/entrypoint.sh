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

# 删除旧数据库，让 alembic 从头创建
# 原因：旧数据库是通过 Base.metadata.create_all() 创建的，
# 与 alembic 迁移的结构不一致，修复成本极高，不如直接重建。
# 新部署的数据库没有重要数据，重建没有损失。
DB_PATH=""
case "$DATABASE_URL" in
    sqlite+aiosqlite:////*)
        DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite+aiosqlite:///||')
        ;;
    *)
        DB_PATH="/app/data/intent_money.db"
        ;;
esac

if [ -f "$DB_PATH" ]; then
    echo "🗑️  删除旧数据库，将从零开始创建..."
    rm -f "$DB_PATH"
    # 清理 SQLite WAL 文件
    rm -f "${DB_PATH}-shm" "${DB_PATH}-wal"
    echo "✅ 旧数据库已删除"
fi

echo "正在执行数据库迁移..."
uv run alembic upgrade head
echo "✅ 数据库迁移完成"

# 启动应用
echo "正在启动应用..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
