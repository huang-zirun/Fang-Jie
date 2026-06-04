#!/bin/bash
# Intent Money OS - 生产环境部署脚本
# 使用方法: bash deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"
BACKEND_DIR="$SCRIPT_DIR/../backend"
ENV_FILE="$BACKEND_DIR/.env"
ENV_PRODUCTION="$BACKEND_DIR/.env.production"

echo "=========================================="
echo "  Intent Money OS - 生产环境部署"
echo "=========================================="

# ========== 1. 检查 .env 文件 ==========
echo ""
echo "📋 步骤 1/6: 检查环境配置..."

if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 .env 文件，从 .env.production 模板创建..."
    if [ -f "$ENV_PRODUCTION" ]; then
        cp "$ENV_PRODUCTION" "$ENV_FILE"
        echo "✅ 已从 .env.production 创建 .env"
        echo "⚠️  请编辑 .env 文件，至少修改以下配置："
        echo "   - SECRET_KEY: 设置为强随机字符串"
        echo "   - AI_API_KEY: 设置你的 OpenRouter API Key"
        echo ""
        echo "编辑完成后重新运行此脚本。"
        exit 1
    else
        echo "❌ 未找到 .env.production 模板，请手动创建 $ENV_FILE"
        exit 1
    fi
fi

# 检查 .env 中是否有 Windows 路径
if grep -qE '[A-Z]:\\\\' "$ENV_FILE" 2>/dev/null; then
    echo "⚠️  检测到 .env 中包含 Windows 路径，正在清理..."
    sed -i 's|^SOCIAL_AUTO_UPLOAD_PATH=.*|SOCIAL_AUTO_UPLOAD_PATH=|' "$ENV_FILE"
    echo "✅ 已清理 Windows 路径"
fi

# 检查关键配置
if grep -q 'SECRET_KEY=change-me\|SECRET_KEY=your-secret-key\|SECRET_KEY=your-88ds9' "$ENV_FILE"; then
    echo "⚠️  SECRET_KEY 仍为默认值，生产环境强烈建议修改！"
fi

echo "✅ 环境配置检查完成"

# ========== 2. 停止旧容器 ==========
echo ""
echo "📋 步骤 2/6: 停止旧容器..."
cd "$SCRIPT_DIR"
docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
echo "✅ 旧容器已停止"

# ========== 3. 备份数据库（如果存在）==========
echo ""
echo "📋 步骤 3/6: 备份数据库..."
mkdir -p "$SCRIPT_DIR/../backups"

# 获取 Compose 项目名（目录名的 小写 形式，Docker Compose 用此作为前缀）
# 当前目录结构是 intent-money/docker/，所以项目名是 docker
PROJECT_NAME="docker"
VOLUME_NAME="${PROJECT_NAME}-db_data"

echo "   查找数据卷: $VOLUME_NAME"

# 尝试备份数据库
if docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
    BACKUP_FILE="intent_money_$(date +%Y%m%d_%H%M%S).db"
    docker run --rm \
        -v "$VOLUME_NAME:/data" \
        -v "$SCRIPT_DIR/../backups:/backup" \
        alpine sh -c "if [ -f /data/intent_money.db ]; then cp /data/intent_money.db /backup/$BACKUP_FILE && echo '✅ 数据库已备份到 backups/$BACKUP_FILE'; else echo 'ℹ️  数据库文件尚不存在（首次部署），跳过备份'; fi"
else
    echo "ℹ️  数据卷 $VOLUME_NAME 不存在（可能首次部署），跳过备份"
    echo "   可用的 Docker volumes:"
    docker volume ls | grep db_data || echo "   (无匹配的 volume)"
fi

# ========== 4. 构建镜像 ==========
echo ""
echo "📋 步骤 4/6: 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build --no-cache
echo "✅ 镜像构建完成"

# ========== 5. 启动服务 ==========
echo ""
echo "📋 步骤 5/6: 启动服务..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ 服务已启动"

# ========== 6. 等待并验证 ==========
echo ""
echo "📋 步骤 6/6: 等待服务就绪并验证..."

# 等待后端健康检查通过
echo "   等待后端启动（最多 180 秒）..."
for i in $(seq 1 36); do
    STATUS=$(docker compose -f docker-compose.prod.yml ps --format json backend 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$STATUS" = "healthy" ]; then
        echo "   ✅ 后端健康检查通过"
        break
    fi
    
    # 检查容器是否崩溃
    RUNNING=$(docker compose -f docker-compose.prod.yml ps backend 2>/dev/null | grep -c "Up\|running" || true)
    if [ "$RUNNING" -eq 0 ] && [ "$STATUS" != "starting" ] && [ "$STATUS" != "unknown" ]; then
        echo "   ❌ 后端容器已停止"
        echo ""
        echo "📋 后端容器日志（最近 50 行）："
        docker compose -f docker-compose.prod.yml logs --tail 50 backend
        exit 1
    fi
    
    if [ $i -eq 36 ]; then
        echo "   ❌ 后端健康检查超时"
        echo ""
        echo "📋 后端容器日志（最近 80 行）："
        docker compose -f docker-compose.prod.yml logs --tail 80 backend
        echo ""
        echo "💡 排查建议："
        echo "   1. 查看完整日志: docker compose -f docker-compose.prod.yml logs backend"
        echo "   2. 检查 .env 配置是否正确"
        echo "   3. 进入容器排查: docker compose -f docker-compose.prod.yml exec backend bash"
        exit 1
    fi
    
    sleep 5
    echo "   ... 等待中 ($((i*5))秒) 状态: $STATUS"
done

# 等待 nginx 就绪
sleep 3

# 验证 nginx 代理
if curl -sf http://localhost:9090/health >/dev/null 2>&1; then
    echo "✅ Nginx 代理健康检查通过"
else
    echo "⚠️  Nginx 代理健康检查失败，后端可能还在启动中"
    echo "   请稍等片刻后手动检查: curl http://localhost:9090/health"
fi

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo ""
echo "📊 服务状态："
docker compose -f docker-compose.prod.yml ps
echo ""
echo "🌐 访问地址: http://localhost:9090"
echo "📋 查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "🔄 重启服务: docker compose -f docker-compose.prod.yml restart"
echo "🛑 停止服务: docker compose -f docker-compose.prod.yml down"
echo ""
