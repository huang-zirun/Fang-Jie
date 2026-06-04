#!/bin/sh
set -e
export PYTHONPATH=/app

# 确保数据目录存在且有正确权限
mkdir -p /app/data

# 输出诊断信息（帮助排查部署问题）
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

# 检查是否存在 alembic_version 记录
STAMP_NEEDED=$(uv run python -c "
import sqlite3, os, sys

db_url = os.environ.get('DATABASE_URL', '')
# 从 DATABASE_URL 提取文件路径
if '////' in db_url:
    db_path = db_url.split('////', 1)[1]
elif '///./' in db_url:
    db_path = db_url.split('///./', 1)[1]
    # 相对路径转为绝对路径
    db_path = os.path.join('/app', db_path)
elif '///' in db_url:
    db_path = db_url.split('///', 1)[1]
else:
    db_path = 'intent_money.db'

if not os.path.exists(db_path):
    # 数据库文件不存在 -> 新数据库，需要完整迁移
    print('migrate')
    sys.exit(0)

conn = sqlite3.connect(db_path)
try:
    # 检查 alembic_version 表是否存在且有记录
    result = conn.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='alembic_version'\").fetchone()
    if result[0] > 0:
        version = conn.execute('SELECT version_num FROM alembic_version').fetchall()
        if version:
            print('has_version')
            sys.exit(0)
    
    # 没有 alembic_version 记录，检查是否有其他表
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\").fetchall()
    table_names = [t[0] for t in tables]
    # 排除 alembic_version 本身
    real_tables = [t for t in table_names if t != 'alembic_version']
    
    if real_tables:
        # 有表但没有版本记录 -> 需要 stamp
        print('stamp_needed')
    else:
        # 空数据库 -> 需要完整迁移
        print('migrate')
finally:
    conn.close()
" 2>&1)

echo "数据库状态检查结果: $STAMP_NEEDED"

case "$STAMP_NEEDED" in
    stamp_needed)
        echo "⚠️  数据库已有表但缺少 alembic 版本记录"
        echo "   正在标记数据库到最新迁移版本（跳过已执行的迁移）..."
        uv run alembic stamp head
        echo "✅ 数据库版本标记完成"
        ;;
    has_version)
        echo "📋 数据库已有 alembic 版本记录，执行增量迁移..."
        uv run alembic upgrade head
        echo "✅ 数据库迁移完成"
        ;;
    migrate)
        echo "🆕 新数据库，执行完整迁移..."
        uv run alembic upgrade head
        echo "✅ 数据库迁移完成"
        ;;
    *)
        echo "⚠️  无法确定数据库状态，尝试直接迁移..."
        uv run alembic upgrade head
        echo "✅ 数据库迁移完成"
        ;;
esac

# 启动应用
echo "正在启动应用..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
