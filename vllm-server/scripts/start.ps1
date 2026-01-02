# ==================================================
# vLLM Server 啟動腳本 (Windows PowerShell)
# ==================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

Write-Host "🚀 啟動 vLLM Server..." -ForegroundColor Cyan

# 檢查 .env 檔案
if (-not (Test-Path ".env")) {
    Write-Host "❌ 錯誤: .env 檔案不存在" -ForegroundColor Red
    Write-Host "   請複製 .env.example 為 .env 並填入配置" -ForegroundColor Yellow
    exit 1
}

# 檢查 Docker 是否運行
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ 錯誤: Docker 未運行，請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 檢查 NVIDIA Container Toolkit
Write-Host "🔍 檢查 GPU 支援..." -ForegroundColor Yellow
$gpuCheck = docker run --rm --runtime=nvidia nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  警告: GPU 測試失敗，但可能仍可運行" -ForegroundColor Yellow
    Write-Host "   錯誤: $gpuCheck" -ForegroundColor Gray
    $continue = Read-Host "是否繼續啟動? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
} else {
    Write-Host "   ✅ GPU 支援正常" -ForegroundColor Green
}

# 檢查 SSL 憑證
if (-not (Test-Path "nginx/certs/cert.pem")) {
    Write-Host "⚠️  SSL 憑證不存在，生成自簽憑證..." -ForegroundColor Yellow
    
    # 確保目錄存在
    New-Item -ItemType Directory -Force -Path "nginx/certs" | Out-Null
    
    # 使用 OpenSSL (需要安裝) 或 PowerShell 生成
    if (Get-Command openssl -ErrorAction SilentlyContinue) {
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
            -keyout "nginx/certs/key.pem" `
            -out "nginx/certs/cert.pem" `
            -subj "/C=TW/ST=Taiwan/L=Taipei/O=Development/CN=localhost"
    } else {
        Write-Host "⚠️  OpenSSL 未安裝，請手動生成 SSL 憑證或安裝 OpenSSL" -ForegroundColor Yellow
        Write-Host "   下載: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    }
}

# 建立必要目錄
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "nginx/logs" | Out-Null

# 啟動服務
Write-Host "📦 拉取最新映像..." -ForegroundColor Cyan
docker compose pull

Write-Host "🔧 啟動容器..." -ForegroundColor Cyan
docker compose up -d

Write-Host ""
Write-Host "✅ vLLM Server 已啟動！" -ForegroundColor Green
Write-Host ""
Write-Host "📍 服務端點:" -ForegroundColor Cyan
Write-Host "   - API:        https://localhost/v1"
Write-Host "   - Health:     https://localhost/health"
Write-Host "   - Metrics:    http://localhost:8000/metrics (內部)"
Write-Host ""
Write-Host "📊 查看日誌:" -ForegroundColor Cyan
Write-Host "   docker compose logs -f vllm"
Write-Host ""
Write-Host "🛑 停止服務:" -ForegroundColor Cyan
Write-Host "   docker compose down"
