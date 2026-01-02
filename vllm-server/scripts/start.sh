#!/bin/bash
# ==================================================
# vLLM Server 啟動腳本
# ==================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 啟動 vLLM Server..."

# 檢查 .env 檔案
if [ ! -f ".env" ]; then
    echo "❌ 錯誤: .env 檔案不存在"
    echo "   請複製 .env.example 為 .env 並填入配置"
    exit 1
fi

# 檢查 SSL 憑證
if [ ! -f "nginx/certs/cert.pem" ]; then
    echo "⚠️  SSL 憑證不存在，生成自簽憑證..."
    bash scripts/generate-certs.sh
fi

# 建立必要目錄
mkdir -p logs nginx/logs

# 啟動服務
echo "📦 拉取最新映像..."
docker compose pull

echo "🔧 啟動容器..."
docker compose up -d

echo ""
echo "✅ vLLM Server 已啟動！"
echo ""
echo "📍 服務端點:"
echo "   - API:        https://localhost/v1"
echo "   - Health:     https://localhost/health"
echo "   - Metrics:    http://localhost:8000/metrics (內部)"
echo ""
echo "📊 查看日誌:"
echo "   docker compose logs -f vllm"
echo ""
echo "🛑 停止服務:"
echo "   docker compose down"
