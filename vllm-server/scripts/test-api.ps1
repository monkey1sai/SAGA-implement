# ==================================================
# vLLM API 測試腳本 (Windows PowerShell)
# ==================================================

param(
    [string]$BaseUrl = "https://localhost",
    [string]$ApiKey = "",
    [switch]$SkipSSL
)

$ErrorActionPreference = "Stop"

# 讀取 .env 檔案取得 API Key
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectDir ".env"

if (-not $ApiKey -and (Test-Path $EnvFile)) {
    $envContent = Get-Content $EnvFile
    foreach ($line in $envContent) {
        if ($line -match "^VLLM_API_KEY=(.+)$") {
            $ApiKey = $matches[1]
            break
        }
    }
}

if (-not $ApiKey) {
    Write-Host "❌ 錯誤: 未提供 API Key" -ForegroundColor Red
    Write-Host "   使用方式: .\test-api.ps1 -ApiKey 'your-api-key'" -ForegroundColor Yellow
    exit 1
}

# 忽略自簽憑證警告
if ($SkipSSL) {
    add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

Write-Host "🧪 測試 vLLM API..." -ForegroundColor Cyan
Write-Host ""

# 測試 1: 健康檢查
Write-Host "1️⃣ 健康檢查..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -SkipCertificateCheck:$SkipSSL
    Write-Host "   ✅ 服務健康" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 服務不可用: $_" -ForegroundColor Red
    exit 1
}

# 測試 2: 模型列表
Write-Host "2️⃣ 取得模型列表..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $ApiKey"
        "Content-Type" = "application/json"
    }
    $models = Invoke-RestMethod -Uri "$BaseUrl/v1/models" -Method Get -Headers $headers -SkipCertificateCheck:$SkipSSL
    Write-Host "   ✅ 可用模型:" -ForegroundColor Green
    foreach ($model in $models.data) {
        Write-Host "      - $($model.id)" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ 取得模型失敗: $_" -ForegroundColor Red
}

# 測試 3: Chat Completion
Write-Host "3️⃣ 測試 Chat Completion..." -ForegroundColor Yellow
try {
    $body = @{
        model = $models.data[0].id
        messages = @(
            @{
                role = "user"
                content = "Hello! Please respond with a short greeting."
            }
        )
        max_tokens = 50
        temperature = 0.7
    } | ConvertTo-Json -Depth 10

    $headers = @{
        "Authorization" = "Bearer $ApiKey"
        "Content-Type" = "application/json"
    }

    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$BaseUrl/v1/chat/completions" -Method Post -Headers $headers -Body $body -SkipCertificateCheck:$SkipSSL
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds

    Write-Host "   ✅ 回應成功 (耗時: $([math]::Round($duration, 2))s)" -ForegroundColor Green
    Write-Host "   📝 回應內容:" -ForegroundColor Cyan
    Write-Host "      $($response.choices[0].message.content)" -ForegroundColor White
    Write-Host ""
    Write-Host "   📊 使用量:" -ForegroundColor Cyan
    Write-Host "      - Prompt tokens: $($response.usage.prompt_tokens)"
    Write-Host "      - Completion tokens: $($response.usage.completion_tokens)"
    Write-Host "      - Total tokens: $($response.usage.total_tokens)"
} catch {
    Write-Host "   ❌ Chat Completion 失敗: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ 測試完成！" -ForegroundColor Green
