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

# 检查并修复数据库迁移状态
uv run python check_db.py

# 启动应用
echo "正在启动应用..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
