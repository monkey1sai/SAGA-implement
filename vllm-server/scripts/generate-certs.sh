#!/bin/bash
# ==================================================
# 自簽 SSL 憑證生成腳本 (開發環境用)
# 生產環境請使用 Let's Encrypt 或正式 CA 憑證
# ==================================================

set -e

CERTS_DIR="$(dirname "$0")/../nginx/certs"
mkdir -p "$CERTS_DIR"

echo "🔐 生成自簽 SSL 憑證..."

# 生成私鑰
openssl genrsa -out "$CERTS_DIR/key.pem" 2048

# 生成憑證簽名請求 (CSR)
openssl req -new -key "$CERTS_DIR/key.pem" \
    -out "$CERTS_DIR/csr.pem" \
    -subj "/C=TW/ST=Taiwan/L=Taipei/O=Development/CN=localhost"

# 生成自簽憑證 (有效期 365 天)
openssl x509 -req -days 365 \
    -in "$CERTS_DIR/csr.pem" \
    -signkey "$CERTS_DIR/key.pem" \
    -out "$CERTS_DIR/cert.pem"

# 清理 CSR
rm "$CERTS_DIR/csr.pem"

echo "✅ 憑證已生成至: $CERTS_DIR"
echo "   - cert.pem (憑證)"
echo "   - key.pem (私鑰)"
echo ""
echo "⚠️  警告: 此為自簽憑證，僅供開發測試使用！"
